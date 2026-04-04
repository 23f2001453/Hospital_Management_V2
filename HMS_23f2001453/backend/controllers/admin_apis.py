# api/admin_apis.py
"""
Admin API — extended endpoints:
  GET  /admin/search                     — universal search across users, departments
  GET  /admin/appointments               — all appointments with filters
  GET  /admin/appointments/<id>/treatment — view any treatment record
  POST /admin/users/<id>/blacklist        — blacklist (deactivate) a user
  POST /admin/users/<id>/unblacklist      — restore a user
  GET  /admin/jobs/<task_id>              — poll Celery task status
"""
import sqlalchemy as sa
from datetime import date, timedelta
from flask import request
from flask_restful import Resource
from flask_security import auth_required, roles_required
from flask_login import current_user

from controllers.database import db
from controllers.models import (
    User, Doctor, Patient, Appointment, Treatment,
    Department, Role, DoctorAvailability
)
from cache import cache
from controllers.config import Config

# ── Helpers ───────────────────────────────────────────────────────────────

def _ok(data, code=200):
    from flask import jsonify, make_response
    return make_response(jsonify(data), code)

def _error(msg, code=400):
    from flask import jsonify, make_response
    return make_response(jsonify({'error': msg}), code)

def _serialize_user(u):
    roles = [r.name for r in u.roles]
    return {
        'id': u.id, 'username': u.username, 'email': u.email,
        'role': roles[0] if roles else None, 'active': u.active,
        'phone': u.phone, 'age': u.age, 'gender': u.gender,
        'doctor': {'id': u.doctor.id, 'specialization': u.doctor.specialization,
                   'experience_years': u.doctor.experience_years,
                   'department_id': u.doctor.department_id} if u.doctor else None,
        'patient': {'id': u.patient.id,
                    'emergency_contact': u.patient.emergency_contact} if u.patient else None,
    }

def _serialize_appt(a):
    return {
        'id': a.id, 'date': str(a.date), 'time': str(a.time)[:5],
        'status': a.status, 'availability_id': a.availability_id,
        'doctor': {
            'id': a.doctor.id,
            'username': a.doctor.user.username if a.doctor and a.doctor.user else None,
            'specialization': a.doctor.specialization,
        } if a.doctor else None,
        'patient': {
            'id': a.patient.id,
            'username': a.patient.user.username if a.patient and a.patient.user else None,
            'email': a.patient.user.email if a.patient and a.patient.user else None,
        } if a.patient else None,
        'treatment': {
            'id': a.treatment.id,
            'diagnosis': a.treatment.diagnosis,
            'prescription': a.treatment.prescription,
            'treatment_notes': a.treatment.treatment_notes,
        } if a.treatment else None,
    }


# ── GET /admin/search ─────────────────────────────────────────────────────
class AdminSearchAPI(Resource):
    """
    Universal search across users, departments, doctors by specialization.

    Query params:
        q    : str  — search term (required, min 2 chars)
        type : str  — filter by type: "doctor" | "patient" | "admin" | "department" (optional)

    Response:
        {
          "query": "card",
          "results": {
            "users":       [...],
            "departments": [...]
          },
          "total": 5
        }
    """
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        q    = (request.args.get('q') or '').strip()
        type_filter = (request.args.get('type') or '').strip().lower()

        if len(q) < 2:
            return _error('Search query must be at least 2 characters.', 400)

        cache_key = f'admin:search:{q}:{type_filter}'
        cached = cache.get(cache_key)
        if cached:
            return _ok(cached)

        pattern = f'%{q}%'
        results = {'users': [], 'departments': []}

        # ── User search ────────────────────────────────────────────────
        user_query = (
            sa.select(User)
            .outerjoin(User.doctor)
            .where(
                sa.or_(
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                    User.phone.ilike(pattern),
                    Doctor.specialization.ilike(pattern),
                )
            )
            .distinct()
        )

        if type_filter in ('doctor', 'patient', 'admin'):
            user_query = (
                user_query
                .join(User.roles)
                .where(Role.name == type_filter)
            )

        users = db.session.scalars(user_query.limit(20)).all()
        results['users'] = [_serialize_user(u) for u in users]

        # ── Department search ──────────────────────────────────────────
        if not type_filter or type_filter == 'department':
            depts = db.session.scalars(
                sa.select(Department).where(Department.name.ilike(pattern)).limit(10)
            ).all()
            results['departments'] = [
                {'id': d.id, 'name': d.name, 'description': d.description,
                 'doctor_count': len(d.doctors)}
                for d in depts
            ]

        total = len(results['users']) + len(results['departments'])
        payload = {'query': q, 'results': results, 'total': total}
        cache.set(cache_key, payload, ttl=60)   # short TTL — search results stale fast
        return _ok(payload)


# ── GET /admin/appointments ───────────────────────────────────────────────
class AdminAppointmentsAPI(Resource):
    """
    All appointments in the system with rich filters.

    Query params (all optional):
        status      : Booked | Confirmed | Treated | Completed | Cancelled
        doctor_id   : int
        patient_id  : int
        from_date   : YYYY-MM-DD
        to_date     : YYYY-MM-DD
        page        : int (default 1)
        per_page    : int (default 20, max 50)

    Response:
        { "appointments": [...], "total": 120, "page": 1, "per_page": 20 }
    """
    @auth_required('token')
    @roles_required('admin')
    def get(self):
        status     = request.args.get('status', '').strip()
        doctor_id  = request.args.get('doctor_id',  type=int)
        patient_id = request.args.get('patient_id', type=int)
        from_date  = request.args.get('from_date',  '').strip()
        to_date    = request.args.get('to_date',    '').strip()
        page       = max(request.args.get('page', 1, type=int), 1)
        per_page   = min(request.args.get('per_page', 20, type=int), 50)

        from datetime import datetime
        query = sa.select(Appointment)

        if status:
            query = query.where(Appointment.status == status)
        if doctor_id:
            query = query.where(Appointment.doctor_id == doctor_id)
        if patient_id:
            query = query.where(Appointment.patient_id == patient_id)
        if from_date:
            try:
                query = query.where(Appointment.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
            except ValueError:
                return _error('Invalid from_date format. Use YYYY-MM-DD.')
        if to_date:
            try:
                query = query.where(Appointment.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
            except ValueError:
                return _error('Invalid to_date format. Use YYYY-MM-DD.')

        total = db.session.scalar(
            sa.select(sa.func.count()).select_from(query.subquery())
        )
        appts = db.session.scalars(
            query.order_by(Appointment.date.desc(), Appointment.time.desc())
                 .offset((page - 1) * per_page)
                 .limit(per_page)
        ).all()

        return _ok({
            'appointments': [_serialize_appt(a) for a in appts],
            'total': total, 'page': page, 'per_page': per_page,
        })


# ── GET /admin/appointments/<id>/treatment ────────────────────────────────
class AdminTreatmentDetailAPI(Resource):
    """
    View the treatment record for any appointment (admin only).

    Response:
        { "treatment": { ... }, "appointment": { ... } }
    """
    @auth_required('token')
    @roles_required('admin')
    def get(self, appointment_id):
        appt = db.session.get(Appointment, appointment_id)
        if not appt:
            return _error('Appointment not found.', 404)

        return _ok({
            'appointment': _serialize_appt(appt),
            'treatment': {
                'id': appt.treatment.id,
                'diagnosis': appt.treatment.diagnosis,
                'prescription': appt.treatment.prescription,
                'treatment_notes': appt.treatment.treatment_notes,
            } if appt.treatment else None,
        })


# ── POST /admin/users/<id>/blacklist ──────────────────────────────────────
class AdminBlacklistAPI(Resource):
    """
    Blacklist (deactivate) a user — they can no longer log in.
    POST → blacklist, DELETE → unblacklist.

    POST body (optional):
        { "reason": "Violated terms of service" }

    Response:
        { "message": "User blacklisted.", "user": { ... } }
    """
    @auth_required('token')
    @roles_required('admin')
    def post(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return _error('User not found.', 404)
        if any(r.name == 'admin' for r in user.roles):
            return _error('Cannot blacklist another admin.', 403)

        user.active = False
        # Rotate the token uniquifier so existing sessions are invalidated immediately
        import uuid
        user.fs_token_uniquifier = str(uuid.uuid4())
        db.session.commit()

        # Bust user cache
        cache.delete(f'user:{user_id}')

        return _ok({'message': f'User {user.username} has been blacklisted.', 'user': _serialize_user(user)})

    @auth_required('token')
    @roles_required('admin')
    def delete(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return _error('User not found.', 404)

        user.active = True
        import uuid
        user.fs_token_uniquifier = str(uuid.uuid4())
        db.session.commit()
        cache.delete(f'user:{user_id}')

        return _ok({'message': f'User {user.username} has been unblacklisted.', 'user': _serialize_user(user)})


# ── GET /admin/jobs/<task_id> ─────────────────────────────────────────────
class AdminJobStatusAPI(Resource):
    """
    Poll the status of any Celery async task by its task_id.
    Used by the frontend after triggering an export to check completion.

    Response:
        {
          "task_id": "abc-123",
          "status":  "PENDING" | "STARTED" | "SUCCESS" | "FAILURE",
          "result":  { ... }   // only present when SUCCESS
        }
    """
    @auth_required('token')
    def get(self, task_id):
        from celery_app import make_celery
        from app import app as flask_app
        celery = make_celery(flask_app)

        result = celery.AsyncResult(task_id)
        payload = {
            'task_id': task_id,
            'status':  result.status,
        }
        if result.successful():
            payload['result'] = result.result
        elif result.failed():
            payload['error'] = str(result.result)

        return _ok(payload)


# ── POST /api/patient/export-csv ─────────────────────────────────────────
class PatientExportCSVAPI(Resource):
    """
    Patient triggers their own CSV export (user-triggered async job).
    Queues a Celery task and immediately returns the task_id.
    The patient polls GET /api/jobs/<task_id> to check when it's done.

    Response:
        { "task_id": "abc-123", "message": "Export queued. You'll receive an email when ready." }
    """
    @auth_required('token')
    def post(self):
        from tasks.export_tasks import export_patient_csv
        task = export_patient_csv.delay(current_user.id)
        return _ok({
            'task_id': task.id,
            'message': 'Export queued. You will receive an email with the CSV once it\'s ready.',
        }, 202)


# ── Route registration ────────────────────────────────────────────────────
def register_admin_routes(api):
    api.add_resource(AdminSearchAPI,          '/admin/search')
    api.add_resource(AdminAppointmentsAPI,    '/admin/appointments')
    api.add_resource(AdminTreatmentDetailAPI, '/admin/appointments/<int:appointment_id>/treatment')
    api.add_resource(AdminBlacklistAPI,       '/admin/users/<int:user_id>/blacklist')
    api.add_resource(AdminJobStatusAPI,       '/jobs/<string:task_id>')
    api.add_resource(PatientExportCSVAPI,     '/patient/export-csv')
