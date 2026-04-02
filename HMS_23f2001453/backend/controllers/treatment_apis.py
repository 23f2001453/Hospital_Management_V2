# app/api/treatment_apis.py
"""
Treatment REST API
==================
Covers diagnosis, prescription, and treatment notes for completed appointments.

Auth: All endpoints require —
    Authentication-Token: <auth_token>

Only a doctor who owns the appointment can create/update a Treatment.
The patient who owns the appointment can read it.
Admins can read any treatment.
"""

import sqlalchemy as sa
from flask import request, current_app
from flask_restful import Resource
from flask_security import auth_required
from flask_login import current_user

from controllers.database import db
from controllers.models import Doctor, Patient, Appointment, Treatment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_treatment(treatment, appt):
    return {
        "treatment_id":    treatment.id,
        "appointment_id":  appt.id,
        "appointment_date": str(appt.date),
        "appointment_time": str(appt.time)[:5],
        "appointment_status": appt.status,
        "doctor_id":       appt.doctor_id,
        "patient_id":      appt.patient_id,
        "diagnosis":       treatment.diagnosis,
        "prescription":    treatment.prescription,
        "treatment_notes": treatment.treatment_notes,
    }


def _error(msg, code=400):
    from flask import jsonify, make_response
    return make_response(jsonify({"error": msg}), code)


def _ok(data, code=200):
    from flask import jsonify, make_response
    return make_response(jsonify(data), code)


def _get_role():
    return [r.name for r in current_user.roles][0] if current_user.roles else None


# ---------------------------------------------------------------------------
# POST /api/doctor/appointments/<appointment_id>/treat
# GET  /api/doctor/appointments/<appointment_id>/treat
# Doctor creates or updates treatment; also views their own treatment record
# ---------------------------------------------------------------------------
class TreatAppointmentAPI(Resource):
    """
    Doctor: Add or update the treatment record for an appointment.
    Creating a treatment automatically moves the appointment status to 'Completed'.

    Headers Required
    ----------------
        Authentication-Token: <doctor_token>

    ── POST (Create treatment) ───────────────────────────────────────────────
    The appointment must be in status 'Treated' before a treatment can be saved.
    (Doctor first transitions the appointment to 'Treated' via the status API,
    then calls this endpoint to save the clinical details.)

    Request Body (JSON):
        {
          "diagnosis":       "Type 2 Diabetes Mellitus",   required
          "prescription":    "Metformin 500mg twice daily", optional
          "treatment_notes": "Follow up in 3 months"        optional
        }

    Success (201):
        { "message": "Treatment saved. Appointment marked Completed.",
          "treatment": { ...treatment object... } }

    ── PUT (Update treatment) ───────────────────────────────────────────────
    Only allowed while appointment status is 'Completed' and treatment exists.
    All fields are optional — only provided fields are updated.

    Request Body (JSON):
        {
          "diagnosis":       "Updated diagnosis",
          "prescription":    "Updated prescription",
          "treatment_notes": "Updated notes"
        }

    Success (200):
        { "message": "Treatment updated.", "treatment": { ...treatment object... } }

    ── GET ──────────────────────────────────────────────────────────────────
    Doctor views the treatment record for one of their appointments.

    Success (200):
        { "treatment": { ...treatment object... } }

    Error Responses
    ---------------
        403  Not a doctor / not your appointment
        404  Appointment or treatment not found
        409  Appointment status is wrong for this action
    """

    @auth_required("token")
    def get(self, appointment_id):
        role = _get_role()
        appt = db.session.get(Appointment, appointment_id)

        if not appt:
            return _error("Appointment not found.", 404)

        # Access control
        if role == "doctor":
            doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
            if not doctor or appt.doctor_id != doctor.id:
                return _error("Access denied.", 403)
        elif role == "patient":
            patient = db.session.scalar(sa.select(Patient).where(Patient.user_id == current_user.id))
            if not patient or appt.patient_id != patient.id:
                return _error("Access denied.", 403)
        elif role != "admin":
            return _error("Access denied.", 403)

        if not appt.treatment:
            return _error("No treatment record found for this appointment.", 404)

        return _ok({"treatment": _serialize_treatment(appt.treatment, appt)})

    @auth_required("token")
    def post(self, appointment_id):
        if _get_role() != "doctor":
            return _error("Only doctors can create treatment records.", 403)

        doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
        appt   = db.session.get(Appointment, appointment_id)

        if not appt or appt.doctor_id != doctor.id:
            return _error("Appointment not found or access denied.", 404)

        if appt.status not in ("Treated", "Confirmed", "Booked"):
            return _error(
                f"Cannot add treatment — appointment status is '{appt.status}'. "
                "Advance the appointment to at least 'Treated' status first.",
                409,
            )

        if appt.treatment:
            return _error(
                "A treatment record already exists for this appointment. "
                "Use PUT to update it.", 409
            )

        data     = request.get_json(silent=True) or {}
        diagnosis       = (data.get("diagnosis")       or "").strip() or None
        prescription    = (data.get("prescription")    or "").strip() or None
        treatment_notes = (data.get("treatment_notes") or "").strip() or None

        if not diagnosis:
            return _error("diagnosis is required.")

        try:
            treatment = Treatment(
                appointment_id=appt.id,
                diagnosis=diagnosis,
                prescription=prescription,
                treatment_notes=treatment_notes,
            )
            db.session.add(treatment)
            appt.status = "Completed"     # auto-complete the appointment
            db.session.commit()
            db.session.refresh(treatment)
            return _ok(
                {
                    "message":   "Treatment saved. Appointment marked Completed.",
                    "treatment": _serialize_treatment(treatment, appt),
                },
                201,
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Treatment save error")
            return _error(f"Failed to save treatment: {str(e)}", 500)

    @auth_required("token")
    def put(self, appointment_id):
        if _get_role() != "doctor":
            return _error("Only doctors can update treatment records.", 403)

        doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
        appt   = db.session.get(Appointment, appointment_id)

        if not appt or appt.doctor_id != doctor.id:
            return _error("Appointment not found or access denied.", 404)

        if not appt.treatment:
            return _error("No treatment record found. Use POST to create one.", 404)

        data = request.get_json(silent=True) or {}

        try:
            if "diagnosis" in data:
                appt.treatment.diagnosis = (data["diagnosis"] or "").strip() or appt.treatment.diagnosis
            if "prescription" in data:
                appt.treatment.prescription = (data["prescription"] or "").strip() or None
            if "treatment_notes" in data:
                appt.treatment.treatment_notes = (data["treatment_notes"] or "").strip() or None

            db.session.commit()
            db.session.refresh(appt.treatment)
            return _ok({
                "message":   "Treatment updated.",
                "treatment": _serialize_treatment(appt.treatment, appt),
            })
        except Exception as e:
            db.session.rollback()
            return _error(f"Update failed: {str(e)}", 500)


# ---------------------------------------------------------------------------
# GET /api/appointments/<appointment_id>/treatment
# Patient views their own treatment record
# ---------------------------------------------------------------------------
class PatientViewTreatmentAPI(Resource):
    """
    Patient: View the treatment/prescription for one of your appointments.

    Headers Required
    ----------------
        Authentication-Token: <patient_token>

    Success Response (200)
    ----------------------
        {
          "treatment": {
            "treatment_id":       4,
            "appointment_id":     5,
            "appointment_date":   "2025-08-15",
            "appointment_time":   "09:00",
            "appointment_status": "Completed",
            "doctor_id":          2,
            "patient_id":         3,
            "diagnosis":          "Type 2 Diabetes Mellitus",
            "prescription":       "Metformin 500mg twice daily",
            "treatment_notes":    "Follow up in 3 months"
          }
        }

    Error Responses
    ---------------
        403  Not a patient / not your appointment
        404  Appointment or treatment not found
    """

    @auth_required("token")
    def get(self, appointment_id):
        role = _get_role()

        appt = db.session.get(Appointment, appointment_id)
        if not appt:
            return _error("Appointment not found.", 404)

        if role == "patient":
            patient = db.session.scalar(sa.select(Patient).where(Patient.user_id == current_user.id))
            if not patient or appt.patient_id != patient.id:
                return _error("Access denied.", 403)
        elif role == "admin":
            pass  # admins can view any
        else:
            return _error("Access denied.", 403)

        if not appt.treatment:
            return _error("Treatment details are not yet available for this appointment.", 404)

        return _ok({"treatment": _serialize_treatment(appt.treatment, appt)})


# ---------------------------------------------------------------------------
# GET /api/doctor/patients/<patient_id>/history
# Doctor views full treatment history for one of their patients
# ---------------------------------------------------------------------------
class PatientTreatmentHistoryAPI(Resource):
    """
    Doctor or Admin: View the complete appointment + treatment history
    for a specific patient.

    Headers Required
    ----------------
        Authentication-Token: <doctor_or_admin_token>

    URL Parameter
    -------------
        patient_id : int  – the Patient.id (not User.id)

    Success Response (200)
    ----------------------
        {
          "patient_id": 3,
          "history": [
            {
              "appointment_id": 5,
              "date": "2025-08-15",
              "time": "09:00",
              "status": "Completed",
              "treatment": {
                "diagnosis": "...",
                "prescription": "...",
                "treatment_notes": "..."
              }
            },
            ...
          ]
        }
    """

    @auth_required("token")
    def get(self, patient_id):
        role = _get_role()

        if role == "doctor":
            doctor = db.session.scalar(sa.select(Doctor).where(Doctor.user_id == current_user.id))
            if not doctor:
                return _error("Doctor profile not found.", 404)
            # Doctor can only view patients that have had an appointment with them
            has_appt = db.session.scalar(
                sa.select(Appointment).where(
                    Appointment.patient_id == patient_id,
                    Appointment.doctor_id == doctor.id,
                )
            )
            if not has_appt:
                return _error("Access denied — this patient has no appointments with you.", 403)

        elif role == "patient":
            # Patients cannot browse other patients
            patient_self = db.session.scalar(sa.select(Patient).where(Patient.user_id == current_user.id))
            if not patient_self or patient_self.id != patient_id:
                return _error("Access denied.", 403)

        elif role != "admin":
            return _error("Access denied.", 403)

        appts = db.session.scalars(
            sa.select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .order_by(Appointment.date.desc(), Appointment.time.desc())
        ).all()

        history = []
        for a in appts:
            entry = {
                "appointment_id": a.id,
                "date":           str(a.date),
                "time":           str(a.time)[:5],
                "status":         a.status,
                "doctor_id":      a.doctor_id,
                "treatment":      None,
            }
            if a.treatment:
                entry["treatment"] = {
                    "diagnosis":       a.treatment.diagnosis,
                    "prescription":    a.treatment.prescription,
                    "treatment_notes": a.treatment.treatment_notes,
                }
            history.append(entry)

        return _ok({"patient_id": patient_id, "history": history})


# ---------------------------------------------------------------------------
# Route Registration Helper
# ---------------------------------------------------------------------------
def register_treatment_routes(api):
    """
    Call this from your app factory alongside the other register_* helpers.

        from app.api.treatment_apis import register_treatment_routes
        register_treatment_routes(api)
    """
    # Doctor manages treatment (create / update / read)
    api.add_resource(
        TreatAppointmentAPI,
        "/doctor/appointments/<int:appointment_id>/treat"
    )
    # Patient reads their own treatment record
    api.add_resource(
        PatientViewTreatmentAPI,
        "/appointments/<int:appointment_id>/treatment"
    )
    # Doctor/Admin reads full history for a patient
    api.add_resource(
        PatientTreatmentHistoryAPI,
        "/doctor/patients/<int:patient_id>/history"
    )
