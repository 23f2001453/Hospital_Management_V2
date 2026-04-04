# tasks/reminder_tasks.py
"""
Daily appointment reminder task.
Runs every morning at 08:00 (configured in celery_app.py beat_schedule).

For each patient who has an appointment TODAY, it sends a reminder email
to their registered email address via MailHog (dev) or real SMTP (prod).
"""
from datetime import date
import sqlalchemy as sa
from flask_mailman import EmailMessage

from celery_app import make_celery
from app import app          # the Flask app instance
from controllers.database import db
from controllers.models import Appointment, Patient, User, Doctor

celery = make_celery(app)


@celery.task(name='tasks.reminder_tasks.send_daily_reminders', bind=True, max_retries=3)
def send_daily_reminders(self):
    """
    Scheduled task — runs daily at 08:00.
    Finds all non-cancelled appointments for today and emails each patient.
    """
    today = date.today()

    appointments = db.session.scalars(
        sa.select(Appointment)
        .where(
            Appointment.date == today,
            Appointment.status.notin_(['Cancelled', 'Completed'])
        )
        .options(
            sa.orm.joinedload(Appointment.patient).joinedload(Patient.user),
            sa.orm.joinedload(Appointment.doctor).joinedload(Doctor.user),
        )
    ).all()

    sent = 0
    errors = []

    for appt in appointments:
        try:
            patient_user = appt.patient.user
            doctor_user  = appt.doctor.user

            subject = f"Reminder: Your appointment today at {appt.time.strftime('%I:%M %p')}"

            body = f"""
Dear {patient_user.username},

This is a friendly reminder that you have a hospital appointment scheduled for today.

  Date : {appt.date.strftime('%d %B %Y')}
  Time : {appt.time.strftime('%I:%M %p')}
  Doctor : Dr. {doctor_user.username}
  Specialization : {appt.doctor.specialization or 'General Practice'}

Please arrive 10 minutes early and bring any relevant medical records.

If you need to cancel, please do so through the MediCore portal as soon as possible.

Stay healthy,
MediCore Team
            """.strip()

            msg = EmailMessage(
                subject=subject,
                body=body,
                to=[patient_user.email],
            )
            msg.send()
            sent += 1

        except Exception as exc:
            errors.append({'appointment_id': appt.id, 'error': str(exc)})

    return {
        'date': str(today),
        'appointments_found': len(appointments),
        'emails_sent': sent,
        'errors': errors,
    }
