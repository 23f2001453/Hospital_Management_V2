# app/api/appointment_apis.py
"""
Appointment & Availability REST API
=====================================
Covers everything a Patient, Doctor, and Admin needs
for the scheduling side of the application.

Auth: All endpoints require the header —
    Authentication-Token: <auth_token>

Date format  : "YYYY-MM-DD"   e.g. "2025-08-15"
Time format  : "HH:MM"        e.g. "09:00"  (24-hour)
"""

import sqlalchemy as sa
from datetime import datetime, date, timedelta

from flask import request, current_app
from flask_restful import Resource
from flask_security import auth_required
from flask_login import current_user

from controllers.database import db
from controllers.models import (
    User, Doctor, Patient,
    Appointment, DoctorAvailability, Department
)


# ---------------------------------------------------------------------------
# Shared serializers
# ---------------------------------------------------------------------------

def _serialize_slot(slot, db_session):
    """Serialize a DoctorAvailability slot with live booking counts."""
    booked = db_session.scalar(
        sa.select(sa.func.count()).select_from(Appointment).where(
            Appointment.availability_id == slot.id,
            Appointment.status != 'Cancelled'
        )
    ) or 0
    capacity  = slot.slot_capacity or 0
    remaining = max(capacity - booked, 0)

    return {
        "id":            slot.id,
        "doctor_id":     slot.doctor_id,
        "date":          str(slot.date),
        "start_time":    str(slot.start_time)[:5],   # "HH:MM"
        "end_time":      str(slot.end_time)[:5],
        "slot_capacity": capacity,
        "booked_count":  booked,
        "remaining":     remaining,
        "is_full":       booked >= capacity if capacity > 0 else False,
        "status":        slot.status,
    }


def _serialize_appointment(appt):
    """Serialize an Appointment with nested doctor/patient summaries."""
    payload = {
        "id":              appt.id,
        "date":            str(appt.date),
        "time":            str(appt.time)[:5],
        "status":          appt.status,
        "availability_id": appt.availability_id,
        "doctor": {
            "id":             appt.doctor.id,
            "user_id":        appt.doctor.user_id,
            "specialization": appt.doctor.specialization,
        } if appt.doctor else None,
        "patient": {
            "id":      appt.patient.id,
            "user_id": appt.patient.user_id,
        } if appt.patient else None,
        "treatment": None,
    }

    if appt.treatment:
        payload["treatment"] = {
            "id":               appt.treatment.id,
            "diagnosis":        appt.treatment.diagnosis,
            "prescription":     appt.treatment.prescription,
            "treatment_notes":  appt.treatment.treatment_notes,
        }

    return payload


def _error(msg, code=400):
    from flask import jsonify, make_response
    return make_response(jsonify({"error": msg}), code)


def _ok(data, code=200):
    from flask import jsonify, make_response
    return make_response(jsonify(data), code)


def _get_role():
    return [r.name for r in current_user.roles][0] if current_user.roles else None


# ---------------------------------------------------------------------------
# GET /api/doctors
# List all doctors (used by patient to browse and book)
# ---------------------------------------------------------------------------
class DoctorListAPI(Resource):
    """
    Public-ish list of all doctors with their department and upcoming
    availability summary.

    Headers Required
    ----------------
        Authentication-Token: <token>

    Query Parameters (optional)
    ---------------------------
        department_id : int
        specialization: str  (partial match)

    Success Response (200)
    ----------------------
        {
          "doctors": [
            {
              "id": 2,
              "user_id": 5,
              "specialization": "Cardiology",
              "experience_years": 10,
              "department_id": 1,
              "department_name": "General Practice",
              "username": "dr_smith"
            },
            ...
          ]
        }
    """

    @auth_required("token")
    def get(self):
        dept_filter  = request.args.get("department_id", type=int)
        spec_filter  = (request.args.get("specialization") or "").strip()

        query = sa.select(Doctor).join(User, Doctor.user_id == User.id)

        if dept_filter:
            query = query.where(Doctor.department_id == dept_filter)
        if spec_filter:
            query = query.where(Doctor.specialization.ilike(f"%{spec_filter}%"))

        doctors = db.session.scalars(query.order_by(User.username)).all()

        result = []
        for doc in doctors:
            result.append({
                "id":               doc.id,
                "user_id":          doc.user_id,
                "username":         doc.user.username if doc.user else None,
                "specialization":   doc.specialization,
                "experience_years": doc.experience_years,
                "department_id":    doc.department_id,
                "department_name":  doc.department.name if doc.department else None,
            })

        return _ok({"doctors": result})


# ---------------------------------------------------------------------------
# GET /api/doctors/<doctor_id>/availability
# List a specific doctor's open slots (used by patient before booking)
# ---------------------------------------------------------------------------
class DoctorAvailabilityListAPI(Resource):
    """
    Returns all OPEN, future availability slots for a given doctor.
    The patient uses this list to pick a slot and then call BookSlotAPI.

    Headers Required
    ----------------
        Authentication-Token: <token>

    URL Parameter
    -------------
        doctor_id : int

    Query Parameters (optional)
    ---------------------------
        date       : "YYYY-MM-DD"  – filter by a specific date
        from_date  : "YYYY-MM-DD"  – start of range (default: today)
        to_date    : "YYYY-MM-DD"  – end of range (default: today + 14 days)

    Success Response (200)
    ----------------------
        {
          "doctor_id": 2,
          "slots": [
            {
              "id": 10,
              "date": "2025-08-15",
              "start_time": "09:00",
              "end_time": "12:00",
              "slot_capacity": 5,
              "booked_count": 2,
              "remaining": 3,
              "is_full": false,
              "status": "open"
            },
            ...
          ]
        }
    """

    @auth_required("token")
    def get(self, doctor_id):
        doctor = db.session.get(Doctor, doctor_id)
        if not doctor:
            return _error("Doctor not found.", 404)

        today    = date.today()
        two_wks  = today + timedelta(days=14)

        from_date = request.args.get("from_date")
        to_date   = request.args.get("to_date")
        exact_date = request.args.get("date")

        try:
            if exact_date:
                from_d = to_d = datetime.strptime(exact_date, "%Y-%m-%d").date()
            else:
                from_d = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else today
                to_d   = datetime.strptime(to_date,   "%Y-%m-%d").date() if to_date   else two_wks
        except ValueError:
            return _error("Invalid date format. Use YYYY-MM-DD.")

        slots = db.session.scalars(
            sa.select(DoctorAvailability).where(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.date >= from_d,
                DoctorAvailability.date <= to_d,
                DoctorAvailability.status == "open",
            ).order_by(DoctorAvailability.date, DoctorAvailability.start_time)
        ).all()

        return _ok({
            "doctor_id": doctor_id,
            "slots": [_serialize_slot(s, db.session) for s in slots],
        })


# ---------------------------------------------------------------------------
# POST /api/doctor/availability          – Doctor creates a slot
# GET  /api/doctor/availability          – Doctor views their own slots
# ---------------------------------------------------------------------------
class ManageAvailabilityAPI(Resource):
    """
    Doctor: create a new availability slot or view your own slots.

    Headers Required
    ----------------
        Authentication-Token: <doctor_token>

    ── GET ──────────────────────────────────────────────────────────────────
    Returns all slots for the logged-in doctor (next 14 days by default).

    Query Parameters (optional):
        from_date : "YYYY-MM-DD"
        to_date   : "YYYY-MM-DD"

    Success (200):
        { "slots": [ ...slot objects... ] }

    ── POST ─────────────────────────────────────────────────────────────────
    Request Body (JSON):
        {
          "date":         "2025-08-15",   required
          "start_time":   "09:00",        required
          "end_time":     "12:00",        required
          "slot_capacity": 5              optional (default 1)
        }

    Success (201):
        { "message": "Slot created.", "slot": { ...slot object... } }

    Errors:
        400  Invalid format, end_time <= start_time, slot in the past,
             overlapping slot
        403  Caller is not a doctor
    """

    @auth_required("token")
    def get(self):
        if _get_role() != "doctor":
            return _error("Only doctors can access this endpoint.", 403)

        doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
        if not doctor:
            return _error("Doctor profile not found.", 404)

        today   = date.today()
        two_wks = today + timedelta(days=14)

        from_date = request.args.get("from_date")
        to_date   = request.args.get("to_date")
        print(f"Doctor {doctor.user.username} is requesting slots from {from_date} to {to_date}.")
        try:
            from_d = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else today
            to_d   = datetime.strptime(to_date,   "%Y-%m-%d").date() if to_date   else two_wks
        except ValueError:
            return _error("Invalid date format. Use YYYY-MM-DD.")

        slots = db.session.scalars(
            sa.select(DoctorAvailability).where(
                DoctorAvailability.doctor_id == doctor.id,
                DoctorAvailability.date >= from_d,
                DoctorAvailability.date <= to_d,
            ).order_by(DoctorAvailability.date, DoctorAvailability.start_time)
        ).all()
        print(f"Doctor {doctor.user.username} has {len(slots)} slots between {from_d} and {to_d}.")
        return _ok({"slots": [_serialize_slot(s, db.session) for s in slots]})

    @auth_required("token")
    def post(self):
        if _get_role() != "doctor":
            return _error("Only doctors can create availability slots.", 403)

        doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
        if not doctor:
            return _error("Doctor profile not found.", 404)

        data     = request.get_json(silent=True) or {}
        date_str = (data.get("date") or "").strip()
        start_str= (data.get("start_time") or "").strip()
        end_str  = (data.get("end_time") or "").strip()
        capacity = data.get("slot_capacity", 1)

        if not all([date_str, start_str, end_str]):
            return _error("date, start_time, and end_time are required.")

        try:
            slot_date  = datetime.strptime(date_str,  "%Y-%m-%d").date()
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time   = datetime.strptime(end_str,   "%H:%M").time()
        except ValueError:
            return _error("Invalid format. Use YYYY-MM-DD for date and HH:MM for times.")

        if start_time >= end_time:
            return _error("end_time must be after start_time.")

        if datetime.combine(slot_date, start_time) < datetime.now():
            return _error("Cannot create a slot in the past.")

        try:
            capacity = int(capacity)
            if capacity < 1:
                raise ValueError
        except (TypeError, ValueError):
            return _error("slot_capacity must be a positive integer.")

        # Overlap check
        overlap = db.session.scalars(
            sa.select(DoctorAvailability).where(
                DoctorAvailability.doctor_id == doctor.id,
                DoctorAvailability.date == slot_date,
                sa.or_(
                    sa.and_(DoctorAvailability.start_time <= start_time, DoctorAvailability.end_time > start_time),
                    sa.and_(DoctorAvailability.start_time < end_time,    DoctorAvailability.end_time >= end_time),
                    sa.and_(DoctorAvailability.start_time >= start_time, DoctorAvailability.end_time <= end_time),
                )
            )
        ).first()

        if overlap:
            return _error("This slot overlaps with an existing availability slot.")

        try:
            new_slot = DoctorAvailability(
                doctor_id=doctor.id,
                date=slot_date,
                start_time=start_time,
                end_time=end_time,
                slot_capacity=capacity,
                status="open",
            )
            db.session.add(new_slot)
            db.session.commit()
            db.session.refresh(new_slot)
            return _ok({"message": "Slot created.", "slot": _serialize_slot(new_slot, db.session)}, 201)
        except Exception as e:
            db.session.rollback()
            return _error(f"Failed to create slot: {str(e)}", 500)


# ---------------------------------------------------------------------------
# PUT  /api/doctor/availability/<slot_id>   – Doctor edits a slot
# DELETE /api/doctor/availability/<slot_id> – Doctor deletes a slot
# ---------------------------------------------------------------------------
class ManageAvailabilityDetailAPI(Resource):
    """
    Doctor: Edit or delete one of your own availability slots.

    Headers Required
    ----------------
        Authentication-Token: <doctor_token>

    ── PUT ──────────────────────────────────────────────────────────────────
    Request Body (JSON) – all fields optional:
        {
          "date":          "2025-08-16",
          "start_time":    "10:00",
          "end_time":      "13:00",
          "slot_capacity": 3,
          "status":        "open"   (or "blocked")
        }

    Rules enforced:
    - Cannot change date/time if the slot has active (non-cancelled) bookings.
    - Cannot reduce capacity below the current number of active bookings.

    Success (200):
        { "message": "Slot updated.", "slot": { ...slot object... } }

    ── DELETE ───────────────────────────────────────────────────────────────
    Cannot delete if there are active bookings. Cancel those first.

    Success (200):
        { "message": "Slot deleted." }
    """

    @auth_required("token")
    def put(self, slot_id):
        if _get_role() != "doctor":
            return _error("Only doctors can edit slots.", 403)

        doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
        slot   = db.session.get(DoctorAvailability, slot_id)

        if not slot or slot.doctor_id != doctor.id:
            return _error("Slot not found or access denied.", 404)

        data = request.get_json(silent=True) or {}

        # How many active bookings exist for this slot?
        active_bookings = db.session.scalar(
            sa.select(sa.func.count()).select_from(Appointment).where(
                Appointment.availability_id == slot.id,
                Appointment.status.notin_(["Cancelled", "Completed"]),
            )
        ) or 0

        # Parse new values (fall back to existing if not provided)
        date_str  = data.get("date")
        start_str = data.get("start_time")
        end_str   = data.get("end_time")

        try:
            new_date  = datetime.strptime(date_str,  "%Y-%m-%d").date() if date_str  else slot.date
            new_start = datetime.strptime(start_str, "%H:%M").time()    if start_str else slot.start_time
            new_end   = datetime.strptime(end_str,   "%H:%M").time()    if end_str   else slot.end_time
        except ValueError:
            return _error("Invalid format. Use YYYY-MM-DD and HH:MM.")

        if new_start >= new_end:
            return _error("end_time must be after start_time.")

        # Guard: cannot shift time if there are active bookings
        if active_bookings > 0:
            time_changed = (
                new_date != slot.date or
                new_start != slot.start_time or
                new_end   != slot.end_time
            )
            if time_changed:
                return _error(
                    f"Cannot change date/time — {active_bookings} active booking(s) exist. "
                    "Cancel those appointments first."
                )

        new_capacity = data.get("slot_capacity")
        if new_capacity is not None:
            try:
                new_capacity = int(new_capacity)
                if new_capacity < 1:
                    raise ValueError
            except (TypeError, ValueError):
                return _error("slot_capacity must be a positive integer.")

            if active_bookings > 0 and new_capacity < active_bookings:
                return _error(
                    f"Cannot reduce capacity below {active_bookings} (current active bookings)."
                )
            slot.slot_capacity = new_capacity

        slot.date       = new_date
        slot.start_time = new_start
        slot.end_time   = new_end

        if "status" in data:
            if data["status"] not in ("open", "blocked"):
                return _error("status must be 'open' or 'blocked'.")
            slot.status = data["status"]

        try:
            db.session.commit()
            db.session.refresh(slot)
            return _ok({"message": "Slot updated.", "slot": _serialize_slot(slot, db.session)})
        except Exception as e:
            db.session.rollback()
            return _error(f"Update failed: {str(e)}", 500)

    @auth_required("token")
    def delete(self, slot_id):
        if _get_role() != "doctor":
            return _error("Only doctors can delete slots.", 403)

        doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
        slot   = db.session.get(DoctorAvailability, slot_id)

        if not slot or slot.doctor_id != doctor.id:
            return _error("Slot not found or access denied.", 404)

        active_bookings = db.session.scalar(
            sa.select(sa.func.count()).select_from(Appointment).where(
                Appointment.availability_id == slot.id,
                Appointment.status.notin_(["Cancelled", "Completed"]),
            )
        ) or 0

        if active_bookings > 0:
            return _error(
                f"Cannot delete slot — {active_bookings} active booking(s) exist. "
                "Cancel those appointments first.", 409
            )

        try:
            db.session.delete(slot)
            db.session.commit()
            return _ok({"message": "Slot deleted."})
        except Exception as e:
            db.session.rollback()
            return _error(f"Delete failed: {str(e)}", 500)


# ---------------------------------------------------------------------------
# POST /api/appointments/book/<slot_id>
# Patient books a specific availability slot
# ---------------------------------------------------------------------------
class BookSlotAPI(Resource):
    """
    Patient: Book an open availability slot by its ID.

    Headers Required
    ----------------
        Authentication-Token: <patient_token>

    URL Parameter
    -------------
        slot_id : int  – the DoctorAvailability.id the patient wants to book

    No request body needed.

    Success Response (201)
    ----------------------
        { "message": "Appointment booked.", "appointment": { ...appointment object... } }

    Error Responses
    ---------------
        403  Caller is not a patient
        404  Slot not found
        409  Slot is full / Slot is blocked / Patient already booked this slot
    """

    @auth_required("token")
    def post(self, slot_id):
        if _get_role() != "patient":
            return _error("Only patients can book appointments.", 403)

        patient = db.session.scalar(sa.select(Patient).where(Patient.user_id == current_user.id))
        if not patient:
            return _error("Patient profile not found.", 404)

        slot = db.session.get(DoctorAvailability, slot_id)
        if not slot:
            return _error("Slot not found.", 404)

        if slot.status != "open":
            return _error("This slot is not open for booking.", 409)

        # Check capacity
        booked_count = db.session.scalar(
            sa.select(sa.func.count()).select_from(Appointment).where(
                Appointment.availability_id == slot.id,
                Appointment.status != "Cancelled",
            )
        ) or 0

        if slot.slot_capacity and booked_count >= slot.slot_capacity:
            return _error("This slot is fully booked.", 409)

        # Prevent double booking
        already_booked = db.session.scalar(
            sa.select(Appointment).where(
                Appointment.availability_id == slot.id,
                Appointment.patient_id == patient.id,
                Appointment.status.in_(["Booked", "Confirmed"]),
            )
        )
        if already_booked:
            return _error("You have already booked this slot.", 409)

        try:
            appt = Appointment(
                patient_id=patient.id,
                doctor_id=slot.doctor_id,
                date=slot.date,
                time=slot.start_time,
                availability_id=slot.id,
                status="Booked",
            )
            db.session.add(appt)
            db.session.commit()
            db.session.refresh(appt)
            return _ok(
                {"message": "Appointment booked.", "appointment": _serialize_appointment(appt)},
                201,
            )
        except Exception as e:
            db.session.rollback()
            return _error(f"Booking failed: {str(e)}", 500)


# ---------------------------------------------------------------------------
# GET  /api/appointments/my             – Patient sees their appointments
# ---------------------------------------------------------------------------
class PatientAppointmentsAPI(Resource):
    """
    Patient: View all your own appointments.

    Headers Required
    ----------------
        Authentication-Token: <patient_token>

    Query Parameters (optional)
    ---------------------------
        status : "Booked" | "Confirmed" | "Treated" | "Completed" | "Cancelled"

    Success Response (200)
    ----------------------
        {
          "appointments": [
            {
              "id": 5,
              "date": "2025-08-15",
              "time": "09:00",
              "status": "Booked",
              "availability_id": 10,
              "doctor": { "id": 2, "specialization": "Cardiology", ... },
              "treatment": null    // or { diagnosis, prescription, treatment_notes }
            },
            ...
          ]
        }
    """

    @auth_required("token")
    def get(self):
        if _get_role() != "patient":
            return _error("Only patients can access this.", 403)

        patient = db.session.scalar(sa.select(Patient).where(Patient.user_id == current_user.id))
        if not patient:
            return _error("Patient profile not found.", 404)

        status_filter = request.args.get("status", "").strip()

        query = sa.select(Appointment).where(Appointment.patient_id == patient.id)
        if status_filter:
            query = query.where(Appointment.status == status_filter)
        query = query.order_by(Appointment.date.desc(), Appointment.time.desc())

        appts = db.session.scalars(query).all()
        return _ok({"appointments": [_serialize_appointment(a) for a in appts]})


# ---------------------------------------------------------------------------
# POST /api/appointments/<appointment_id>/cancel
# Patient cancels their own appointment
# ---------------------------------------------------------------------------
class PatientCancelAppointmentAPI(Resource):
    """
    Patient: Cancel one of your own appointments.
    Only appointments with status "Booked" can be cancelled.

    Headers Required
    ----------------
        Authentication-Token: <patient_token>

    No request body needed.

    Success Response (200)
    ----------------------
        { "message": "Appointment cancelled.", "appointment": { ...appointment object... } }

    Error Responses
    ---------------
        403  Not a patient / trying to cancel someone else's appointment
        404  Appointment not found
        409  Appointment status is not "Booked" (already completed/cancelled)
    """

    @auth_required("token")
    def post(self, appointment_id):
        if _get_role() != "patient":
            return _error("Only patients can cancel appointments.", 403)

        patient = db.session.scalar(sa.select(Patient).where(Patient.user_id == current_user.id))
        appt    = db.session.get(Appointment, appointment_id)

        if not appt:
            return _error("Appointment not found.", 404)

        if appt.patient_id != patient.id:
            return _error("You can only cancel your own appointments.", 403)

        if appt.status != "Booked":
            return _error(
                f"Cannot cancel — appointment status is '{appt.status}'. "
                "Only 'Booked' appointments can be cancelled.", 409
            )

        try:
            appt.status = "Cancelled"
            db.session.commit()
            db.session.refresh(appt)
            return _ok({"message": "Appointment cancelled.", "appointment": _serialize_appointment(appt)})
        except Exception as e:
            db.session.rollback()
            return _error(f"Cancellation failed: {str(e)}", 500)


# ---------------------------------------------------------------------------
# GET  /api/doctor/appointments         – Doctor sees their own appointments
# POST /api/doctor/appointments/<id>/status – Doctor updates appointment status
# ---------------------------------------------------------------------------
class DoctorAppointmentsAPI(Resource):
    """
    Doctor: View all appointments assigned to you.

    Headers Required
    ----------------
        Authentication-Token: <doctor_token>

    Query Parameters (optional)
    ---------------------------
        status     : filter by status string
        from_date  : "YYYY-MM-DD"
        to_date    : "YYYY-MM-DD"

    Success Response (200)
    ----------------------
        { "appointments": [ ...appointment objects... ] }
    """

    @auth_required("token")
    def get(self):
        if _get_role() != "doctor":
            return _error("Only doctors can access this.", 403)

        doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
        if not doctor:
            return _error("Doctor profile not found.", 404)

        status_filter = request.args.get("status", "").strip()
        from_date     = request.args.get("from_date")
        to_date       = request.args.get("to_date")

        query = sa.select(Appointment).where(Appointment.doctor_id == doctor.id)

        if status_filter:
            query = query.where(Appointment.status == status_filter)

        try:
            if from_date:
                query = query.where(Appointment.date >= datetime.strptime(from_date, "%Y-%m-%d").date())
            if to_date:
                query = query.where(Appointment.date <= datetime.strptime(to_date, "%Y-%m-%d").date())
        except ValueError:
            return _error("Invalid date format. Use YYYY-MM-DD.")

        query = query.order_by(Appointment.date, Appointment.time)
        appts = db.session.scalars(query).all()
        return _ok({"appointments": [_serialize_appointment(a) for a in appts]})


class DoctorUpdateAppointmentStatusAPI(Resource):
    """
    Doctor: Advance an appointment through the status workflow.

    Status Transitions (strict):
        Booked    → Confirmed | Cancelled
        Confirmed → Treated   | Cancelled
        Treated   → Completed
        Completed → (terminal — no further changes)
        Cancelled → (terminal — no further changes)

    Headers Required
    ----------------
        Authentication-Token: <doctor_token>

    Request Body (JSON):
        { "status": "Confirmed" }

    Success Response (200)
    ----------------------
        { "message": "Status updated.", "appointment": { ...appointment object... } }

    Error Responses
    ---------------
        400  Invalid or disallowed status transition
        403  Not a doctor / not your appointment
        404  Appointment not found
    """

    ALLOWED_TRANSITIONS = {
        "Booked":    ["Confirmed", "Cancelled"],
        "Confirmed": ["Treated",   "Cancelled"],
        "Treated":   ["Completed"],
        "Completed": [],
        "Cancelled": [],
    }

    @auth_required("token")
    def post(self, appointment_id):
        if _get_role() != "doctor":
            return _error("Only doctors can update appointment status.", 403)

        doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
        appt   = db.session.get(Appointment, appointment_id)

        if not appt or appt.doctor_id != doctor.id:
            return _error("Appointment not found or access denied.", 404)

        data       = request.get_json(silent=True) or {}
        new_status = (data.get("status") or "").strip()

        allowed = self.ALLOWED_TRANSITIONS.get(appt.status, [])
        if new_status not in allowed:
            return _error(
                f"Cannot transition from '{appt.status}' to '{new_status}'. "
                f"Allowed next statuses: {allowed}",
                400,
            )

        try:
            appt.status = new_status
            db.session.commit()
            db.session.refresh(appt)
            return _ok({"message": f"Status updated to '{new_status}'.", "appointment": _serialize_appointment(appt)})
        except Exception as e:
            db.session.rollback()
            return _error(f"Update failed: {str(e)}", 500)


# ---------------------------------------------------------------------------
# GET  /api/doctor/patients
# Doctor sees the distinct list of all patients they've ever had
# ---------------------------------------------------------------------------
class DoctorPatientListAPI(Resource):
    """
    Doctor: List all unique patients who have had an appointment with you.

    Headers Required
    ----------------
        Authentication-Token: <doctor_token>

    Success Response (200)
    ----------------------
        {
          "patients": [
            {
              "patient_id": 3,
              "user_id": 7,
              "username": "john_doe",
              "email": "john@example.com",
              "age": 30,
              "gender": "Male",
              "phone": "9876543210",
              "emergency_contact": "9111111111"
            },
            ...
          ]
        }
    """

    @auth_required("token")
    def get(self):
        if _get_role() != "doctor":
            return _error("Only doctors can access this.", 403)

        doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
        if not doctor:
            return _error("Doctor profile not found.", 404)

        patients = db.session.scalars(
            sa.select(Patient)
            .join(Appointment, Appointment.patient_id == Patient.id)
            .where(Appointment.doctor_id == doctor.id)
            .group_by(Patient.id)
        ).all()

        result = []
        for p in patients:
            result.append({
                "patient_id":        p.id,
                "user_id":           p.user_id,
                "username":          p.user.username if p.user else None,
                "email":             p.user.email    if p.user else None,
                "age":               p.user.age      if p.user else None,
                "gender":            p.user.gender   if p.user else None,
                "phone":             p.user.phone    if p.user else None,
                "emergency_contact": p.emergency_contact,
            })

        return _ok({"patients": result})


# ---------------------------------------------------------------------------
# Route Registration Helper
# ---------------------------------------------------------------------------
def register_appointment_routes(api):
    """
    Call this from your app factory.

        from app.api.appointment_apis import register_appointment_routes
        register_appointment_routes(api)
    """
    # Browsing
    api.add_resource(DoctorListAPI,                    "/doctors")
    api.add_resource(DoctorAvailabilityListAPI,        "/doctors/<int:doctor_id>/availability")

    # Doctor manages their own slots
    api.add_resource(ManageAvailabilityAPI,            "/doctor/availability")
    api.add_resource(ManageAvailabilityDetailAPI,      "/doctor/availability/<int:slot_id>")

    # Doctor views and manages their appointments
    api.add_resource(DoctorAppointmentsAPI,            "/doctor/appointments")
    api.add_resource(DoctorUpdateAppointmentStatusAPI, "/doctor/appointments/<int:appointment_id>/status")
    api.add_resource(DoctorPatientListAPI,             "/doctor/patients")

    # Patient actions
    api.add_resource(BookSlotAPI,                      "/appointments/book/<int:slot_id>")
    api.add_resource(PatientAppointmentsAPI,           "/appointments/my")
    api.add_resource(PatientCancelAppointmentAPI,      "/appointments/<int:appointment_id>/cancel")
