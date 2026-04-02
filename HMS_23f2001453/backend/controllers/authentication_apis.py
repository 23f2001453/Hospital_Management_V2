# app/api/authentication_apis.py
"""
Authentication & User Management REST API
==========================================
All endpoints return JSON. Requires Flask-RESTful, Flask-Security-Too,
and a configured `user_datastore` (SQLAlchemyUserDatastore) plus `db`
imported from your app's database controller.

Token strategy: Flask-Security-Too's built-in token auth is used.
  - After login, the client receives an `auth_token`.
  - Protected endpoints expect the header:
      Authentication-Token: <auth_token>
"""

import uuid
import sqlalchemy as sa
from flask import request, jsonify, make_response, current_app
from flask_restful import Resource
from flask_login import login_user, logout_user, current_user
from controllers.user_datastore import user_datastore
from flask_security import auth_required, roles_required, roles_accepted

from controllers.database import db
from controllers.models import User, Doctor, Patient, Department, Role


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_payload(user):
    """Serialize a User object into a safe dict for API responses."""
    roles = [r.name for r in user.roles]
    role  = roles[0] if roles else None          # primary role string

    payload = {
        "id":       user.id,
        "username": user.username,
        "email":    user.email,
        "role":     role,
        "roles":    roles,
        "age":      user.age,
        "gender":   user.gender,
        "phone":    user.phone,
        "address":  user.address,
        "active":   user.active,
    }

    if user.doctor:
        payload["doctor"] = {
            "id":               user.doctor.id,
            "specialization":   user.doctor.specialization,
            "experience_years": user.doctor.experience_years,
            "department_id":    user.doctor.department_id,
        }

    if user.patient:
        payload["patient"] = {
            "id":                user.patient.id,
            "emergency_contact": user.patient.emergency_contact,
        }

    return payload


def _error(message, code=400):
    return make_response(jsonify({"error": message}), code)


def _ok(data, code=200):
    return make_response(jsonify(data), code)


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------
class RegisterAPI(Resource):
    """
    Register a new user as either a 'patient' or a 'doctor'.

    Request Body (JSON)
    -------------------
    Required for both roles:
        username        : str   – unique login name
        email           : str   – unique email address
        password        : str   – min 6 characters
        confirm_password: str   – must match password
        role            : str   – "patient" | "doctor"
        first_name      : str
        last_name       : str
        age             : int
        gender          : str   – "Male" | "Female" | "Other"
        phone           : str
        address         : str

    Extra field for role == "patient":
        emergency_contact: str  – phone / name of emergency contact

    Extra fields for role == "doctor":
        specialization  : str
        experience_years: int
        availability    : str   – free-text fallback (optional)

    Success Response (201)
    ----------------------
        { "message": "Account created successfully.", "user": { ...user payload... } }

    Error Responses
    ---------------
        400  Missing/invalid fields, duplicate username/email, unknown role
    """

    def post(self):
        data = request.get_json(silent=True) or {}

        # ── Required base fields ──────────────────────────────────────────
        username         = (data.get("username") or "").strip()
        email            = (data.get("email") or "").strip()
        password         = data.get("password", "")
        confirm_password = data.get("confirm_password", "")
        role             = (data.get("role") or "").strip().lower()

        if not all([username, email, password, confirm_password, role]):
            return _error("username, email, password, confirm_password, and role are required.")

        if len(password) < 6:
            return _error("Password must be at least 6 characters.")

        if password != confirm_password:
            return _error("Passwords do not match.")

        if role not in ("patient", "doctor"):
            return _error("role must be 'patient' or 'doctor'.")

        # ── Personal fields ───────────────────────────────────────────────
        first_name = (data.get("first_name") or "").strip()
        last_name  = (data.get("last_name") or "").strip()
        phone      = (data.get("phone") or "").strip()
        address    = (data.get("address") or "").strip()
        gender     = (data.get("gender") or "").strip()
        age_raw    = data.get("age")

        if not all([first_name, last_name, phone, address, gender]):
            return _error("first_name, last_name, phone, address, and gender are required.")

        try:
            age = int(age_raw)
            if not (1 <= age <= 120):
                raise ValueError
        except (TypeError, ValueError):
            return _error("age must be an integer between 1 and 120.")

        # ── Duplicate check ───────────────────────────────────────────────
        existing = db.session.scalar(
            sa.select(User).where(
                sa.or_(User.username == username, User.email == email)
            )
        )
        if existing:
            field = "username" if existing.username == username else "email"
            return _error(f"That {field} is already registered.")

        try:
            # ── Create base User ──────────────────────────────────────────
            new_user = user_datastore.create_user(
                username=username,
                email=email,
                password=password,          # Flask-Security hashes this
                active=True,
                fs_uniquifier=str(uuid.uuid4()),
                fs_token_uniquifier=str(uuid.uuid4()),
            )
            new_user.age      = age
            new_user.gender   = gender
            new_user.phone    = phone
            new_user.address  = address

            # ── Assign role ───────────────────────────────────────────────
            user_datastore.add_role_to_user(new_user, role)
            db.session.flush()   # get new_user.id before creating profile

            # ── Role-specific profile ─────────────────────────────────────
            if role == "patient":
                emergency_contact = (data.get("emergency_contact") or "").strip()
                patient_profile = Patient(
                    user_id=new_user.id,
                    emergency_contact=emergency_contact or None,
                )
                db.session.add(patient_profile)

            elif role == "doctor":
                specialization   = (data.get("specialization") or "").strip()
                experience_raw   = data.get("experience_years", 0)
                availability_txt = (data.get("availability") or "").strip()

                try:
                    experience_years = int(experience_raw)
                except (TypeError, ValueError):
                    experience_years = 0

                # Try to attach to default department
                department = db.session.scalar(
                    sa.select(Department).where(Department.name == "General Practice")
                )

                doctor_profile = Doctor(
                    user_id=new_user.id,
                    specialization=specialization or None,
                    experience_years=experience_years,
                    availability=availability_txt or None,
                    department=department,
                )
                db.session.add(doctor_profile)

            db.session.commit()
            db.session.refresh(new_user)

            return _ok(
                {
                    "message": "Account created successfully.",
                    "user": _user_payload(new_user),
                },
                201,
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Registration error")
            return _error(f"Registration failed: {str(e)}", 500)


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------
class LoginAPI(Resource):
    """
    Authenticate a user and return their auth token.

    Request Body (JSON)
    -------------------
        email   : str
        password: str

    Success Response (200)
    ----------------------
        {
          "message": "Login successful.",
          "auth_token": "<token>",
          "user": { ...user payload... }
        }

    The auth_token must be sent in every subsequent protected request as:
        Authentication-Token: <auth_token>

    Error Responses
    ---------------
        400  Missing fields
        401  Invalid credentials or inactive account
    """

    def post(self):
        data = request.get_json(silent=True) or {}

        email    = (data.get("email") or "").strip()
        password = data.get("password", "")

        if not email or not password:
            return _error("email and password are required.")

        user = user_datastore.find_user(email=email)

        if not user:
            return _error("Invalid email or password.", 401)

        if not user.active:
            return _error("Account is deactivated. Contact admin.", 401)

        # Flask-Security-Too stores password as a hash via `password` column
        from flask_security import verify_password
        if not verify_password(password, user.password):
            return _error("Invalid email or password.", 401)

        # Use Flask-Security token auth (stored in fs_token_uniquifier)
        auth_token = user.get_auth_token()
        login_user(user)

        return _ok(
            {
                "message":    "Login successful.",
                "auth_token": auth_token,
                "user":       _user_payload(user),
            }
        )


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------
class LogoutAPI(Resource):
    """
    Invalidate the current user session.

    Headers Required
    ----------------
        Authentication-Token: <auth_token>

    Success Response (200)
    ----------------------
        { "message": "Logged out successfully." }
    """

    @auth_required("token")
    def post(self):
        logout_user()
        return _ok({"message": "Logged out successfully."})


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------
class MeAPI(Resource):
    """
    Return the authenticated user's full profile.

    Headers Required
    ----------------
        Authentication-Token: <auth_token>

    Success Response (200)
    ----------------------
        { "user": { ...user payload... } }
    """

    @auth_required("token")
    def get(self):
        return _ok({"user": _user_payload(current_user)})


# ---------------------------------------------------------------------------
# PUT /api/auth/me  (update own profile)
# ---------------------------------------------------------------------------
class UpdateProfileAPI(Resource):
    """
    Update the authenticated user's own profile.

    Headers Required
    ----------------
        Authentication-Token: <auth_token>

    Request Body (JSON) – all fields optional; only provided fields are updated
    -------------------
        first_name      : str
        last_name       : str
        age             : int
        gender          : str
        phone           : str
        address         : str
        password        : str  (min 6 chars; also send confirm_password)
        confirm_password: str

    Role-specific optional fields:
        For patients —
            emergency_contact: str
        For doctors —
            specialization   : str
            experience_years : int
            availability     : str

    Success Response (200)
    ----------------------
        { "message": "Profile updated.", "user": { ...user payload... } }
    """

    @auth_required("token")
    def put(self):
        data = request.get_json(silent=True) or {}
        user = current_user

        try:
            # ── Optional personal fields ──────────────────────────────────
            if "age" in data:
                try:
                    age = int(data["age"])
                    if not (1 <= age <= 120):
                        raise ValueError
                    user.age = age
                except (TypeError, ValueError):
                    return _error("age must be an integer between 1 and 120.")

            for field in ("gender", "phone", "address"):
                if field in data:
                    setattr(user, field, (data[field] or "").strip() or None)

            # ── Password change ───────────────────────────────────────────
            if "password" in data:
                password         = data["password"]
                confirm_password = data.get("confirm_password", "")
                if len(password) < 6:
                    return _error("Password must be at least 6 characters.")
                if password != confirm_password:
                    return _error("Passwords do not match.")
                from flask_security.utils import hash_password
                user.password = hash_password(password)

            # ── Role-specific updates ─────────────────────────────────────
            roles = [r.name for r in user.roles]

            if "patient" in roles and user.patient:
                if "emergency_contact" in data:
                    user.patient.emergency_contact = (
                        data["emergency_contact"] or ""
                    ).strip() or None

            if "doctor" in roles and user.doctor:
                if "specialization" in data:
                    user.doctor.specialization = (
                        data["specialization"] or ""
                    ).strip() or None
                if "experience_years" in data:
                    try:
                        user.doctor.experience_years = int(data["experience_years"])
                    except (TypeError, ValueError):
                        return _error("experience_years must be an integer.")
                if "availability" in data:
                    user.doctor.availability = (
                        data["availability"] or ""
                    ).strip() or None

            db.session.commit()
            db.session.refresh(user)
            return _ok({"message": "Profile updated.", "user": _user_payload(user)})

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Profile update error")
            return _error(f"Update failed: {str(e)}", 500)


# ---------------------------------------------------------------------------
# Admin: GET /api/admin/users
# ---------------------------------------------------------------------------
class AdminUserListAPI(Resource):
    """
    List all users. Admin only.

    Headers Required
    ----------------
        Authentication-Token: <auth_token>   (must belong to an admin)

    Query Parameters (all optional)
    --------------------------------
        role    : str  – filter by role: "patient" | "doctor" | "admin"
        page    : int  – page number (default 1)
        per_page: int  – results per page (default 20, max 100)

    Success Response (200)
    ----------------------
        {
          "users": [ ...user payload... ],
          "total": 42,
          "page": 1,
          "per_page": 20
        }
    """

    @auth_required("token")
    @roles_required("admin")
    def get(self):
        role_filter = request.args.get("role", "").strip().lower()
        page        = max(int(request.args.get("page", 1)), 1)
        per_page    = min(int(request.args.get("per_page", 20)), 100)

        query = sa.select(User)

        if role_filter:
            query = query.join(User.roles).where(Role.name == role_filter)

        total = db.session.scalar(
            sa.select(sa.func.count()).select_from(query.subquery())
        )

        users = db.session.scalars(
            query.offset((page - 1) * per_page).limit(per_page)
        ).all()

        return _ok(
            {
                "users":    [_user_payload(u) for u in users],
                "total":    total,
                "page":     page,
                "per_page": per_page,
            }
        )


# ---------------------------------------------------------------------------
# Admin: GET/PUT/DELETE /api/admin/users/<int:user_id>
# ---------------------------------------------------------------------------
class AdminUserDetailAPI(Resource):
    """
    Retrieve, edit, or delete any user. Admin only.

    Headers Required
    ----------------
        Authentication-Token: <auth_token>   (must belong to an admin)

    GET  → returns full user payload
    PUT  → same body as UpdateProfileAPI plus 'active' (bool) and 'role' (str)
    DELETE → permanently deletes user and their role-specific profile
    """

    @auth_required("token")
    @roles_required("admin")
    def get(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return _error("User not found.", 404)
        return _ok({"user": _user_payload(user)})

    @auth_required("token")
    @roles_required("admin")
    def put(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return _error("User not found.", 404)

        data = request.get_json(silent=True) or {}

        try:
            for field in ("age", "gender", "phone", "address"):
                if field in data:
                    val = data[field]
                    if field == "age":
                        try:
                            val = int(val)
                            if not (1 <= val <= 120):
                                raise ValueError
                        except (TypeError, ValueError):
                            return _error("age must be 1–120.")
                    setattr(user, field, val)

            if "active" in data:
                user.active = bool(data["active"])

            if "password" in data:
                from flask_security.utils import hash_password
                user.password = hash_password(data["password"])

            # Role change
            if "role" in data:
                new_role = data["role"].strip().lower()
                if new_role not in ("patient", "doctor", "admin"):
                    return _error("Invalid role.")
                for r in user.roles:
                    user_datastore.remove_role_from_user(user, r.name)
                user_datastore.add_role_to_user(user, new_role)

            # Doctor-specific
            if user.doctor and "specialization" in data:
                user.doctor.specialization = data["specialization"]
            if user.doctor and "experience_years" in data:
                user.doctor.experience_years = int(data["experience_years"])

            # Patient-specific
            if user.patient and "emergency_contact" in data:
                user.patient.emergency_contact = data["emergency_contact"]

            db.session.commit()
            db.session.refresh(user)
            return _ok({"message": "User updated.", "user": _user_payload(user)})

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Admin user update error")
            return _error(f"Update failed: {str(e)}", 500)

    @auth_required("token")
    @roles_required("admin")
    def delete(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return _error("User not found.", 404)

        try:
            db.session.delete(user)   # cascade deletes Doctor/Patient profiles
            db.session.commit()
            return _ok({"message": f"User {user_id} deleted."})
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Admin delete error")
            return _error(f"Delete failed: {str(e)}", 500)


# ---------------------------------------------------------------------------
# Route Registration Helper
# ---------------------------------------------------------------------------
def register_auth_routes(api):
    """
    Call this from your app factory after creating the Flask-RESTful Api object.

    Example
    -------
        from flask_restful import Api
        from app.api.authentication_apis import register_auth_routes

        api = Api(app, prefix='/api')
        register_auth_routes(api)
    """
    api.add_resource(RegisterAPI,        "/auth/register")
    api.add_resource(LoginAPI,           "/auth/login")
    api.add_resource(LogoutAPI,          "/auth/logout")
    api.add_resource(MeAPI,              "/auth/me")
    api.add_resource(UpdateProfileAPI,   "/auth/me")   # same URL, different method
    api.add_resource(AdminUserListAPI,   "/admin/users")
    api.add_resource(AdminUserDetailAPI, "/admin/users/<int:user_id>")
