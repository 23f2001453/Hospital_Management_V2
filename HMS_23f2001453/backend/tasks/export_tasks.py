# tasks/export_tasks.py
"""
Patient CSV export task — user-triggered async job.

When a patient requests their treatment history export:
  1. A Celery task is queued immediately (returns task_id to frontend)
  2. The task runs in the background, builds the CSV
  3. Sends an email with the CSV attached to the patient
  4. Frontend can poll GET /api/jobs/<task_id> for status
"""
import csv
import io
import sqlalchemy as sa
from flask_mailman import EmailMessage

from celery_app import make_celery
from app import app
from controllers.database import db
from controllers.models import Appointment, Patient, User, Doctor, Treatment

celery = make_celery(app)


@celery.task(name='tasks.export_tasks.export_patient_csv', bind=True, max_retries=3)
def export_patient_csv(self, patient_user_id: int):
    """
    User-triggered async task.
    Builds a full treatment history CSV for the patient and emails it to them.

    Returns a dict with status so the frontend can poll for completion.
    """
    try:
        user = db.session.get(User, patient_user_id)
        if not user or not user.patient:
            return {'status': 'error', 'message': 'Patient not found'}

        patient = user.patient

        appointments = db.session.scalars(
            sa.select(Appointment)
            .where(Appointment.patient_id == patient.id)
            .options(
                sa.orm.joinedload(Appointment.doctor).joinedload(Doctor.user),
                sa.orm.joinedload(Appointment.treatment),
            )
            .order_by(Appointment.date.desc())
        ).all()

        # Build CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'appointment_id',
            'user_id',
            'username',
            'patient_email',
            'consulting_doctor',
            'doctor_specialization',
            'appointment_date',
            'appointment_time',
            'appointment_status',
            'diagnosis',
            'treatment_given',
            'prescription',
            'next_visit_notes',
        ])

        for appt in appointments:
            tx = appt.treatment
            writer.writerow([
                appt.id,
                user.id,
                user.username,
                user.email,
                appt.doctor.user.username if appt.doctor and appt.doctor.user else '',
                appt.doctor.specialization if appt.doctor else '',
                str(appt.date),
                str(appt.time),
                appt.status,
                tx.diagnosis        if tx else '',
                tx.treatment_notes  if tx else '',
                tx.prescription     if tx else '',
                '',   # next_visit — extend model if needed
            ])

        csv_content = output.getvalue()
        filename    = f"treatment_history_{user.username}.csv"

        # flask-mailman: attach(filename, content, mimetype)
        # content must be a plain string for text/csv — not bytes
        msg = EmailMessage(
            subject='MediCore — Your Treatment History Export',
            body=f"""Dear {user.username},

Your treatment history export is ready. Please find the CSV file attached to this email.

This file contains all your appointment records including diagnosis and prescription details.

Stay healthy,
MediCore Team""",
            to=[user.email],
        )
        msg.attach(filename, csv_content, 'text/csv')
        msg.send()

        return {
            'status': 'success',
            'message': f'Export emailed to {user.email}',
            'rows': len(appointments),
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)