# tasks/report_tasks.py
"""
Monthly doctor activity report task.
Runs on the 1st of every month at 06:00 (beat_schedule in celery_app.py).

For each doctor, it:
  1. Collects all appointments from the previous calendar month
  2. Builds an HTML report with appointment stats, diagnoses, treatments
  3. Emails the HTML report to the doctor
"""
from datetime import date, timedelta
from calendar import monthrange
import sqlalchemy as sa
from flask_mailman import EmailMessage

from celery_app import make_celery
from app import app
from controllers.database import db
from controllers.models import Appointment, Doctor, Patient, User, Treatment

celery = make_celery(app)


def _build_html_report(doctor_user, doctor, appointments, month_label):
    """Build the HTML email body for the monthly report."""
    total       = len(appointments)
    completed   = [a for a in appointments if a.status == 'Completed']
    cancelled   = [a for a in appointments if a.status == 'Cancelled']
    with_rx     = [a for a in completed if a.treatment]

    rows = ''.join(
        f"""<tr>
              <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0">{a.date}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0">{a.patient.user.username}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0">{a.status}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0">{a.treatment.diagnosis if a.treatment else '—'}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #e2e8f0">{a.treatment.prescription if a.treatment else '—'}</td>
            </tr>"""
        for a in appointments
    )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Monthly Activity Report</title></head>
<body style="font-family:sans-serif;color:#0f172a;max-width:800px;margin:0 auto;padding:32px">

  <div style="border-bottom:3px solid #0d9488;padding-bottom:16px;margin-bottom:24px">
    <h1 style="font-size:24px;margin:0;color:#0d9488">MediCore</h1>
    <h2 style="font-size:18px;margin:8px 0 0;color:#334155">Monthly Activity Report — {month_label}</h2>
  </div>

  <p style="color:#334155">Dear Dr. {doctor_user.username},</p>
  <p style="color:#64748b">Here is your activity summary for {month_label}.</p>

  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0">
    {"".join(f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px;text-align:center"><div style="font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#64748b;margin-bottom:8px">{label}</div><div style="font-size:28px;font-weight:600;color:#0f172a">{val}</div></div>'
    for label, val in [
        ('Total appointments', total),
        ('Completed', len(completed)),
        ('Cancelled', len(cancelled)),
        ('Treatments issued', len(with_rx)),
    ])}
  </div>

  <h3 style="font-size:15px;margin:24px 0 12px;color:#0f172a">Appointment details</h3>
  <table style="width:100%;border-collapse:collapse;font-size:13px">
    <thead>
      <tr style="background:#f1f5f9">
        <th style="padding:10px 12px;text-align:left;font-weight:600;color:#64748b">Date</th>
        <th style="padding:10px 12px;text-align:left;font-weight:600;color:#64748b">Patient</th>
        <th style="padding:10px 12px;text-align:left;font-weight:600;color:#64748b">Status</th>
        <th style="padding:10px 12px;text-align:left;font-weight:600;color:#64748b">Diagnosis</th>
        <th style="padding:10px 12px;text-align:left;font-weight:600;color:#64748b">Prescription</th>
      </tr>
    </thead>
    <tbody>
      {rows if rows else '<tr><td colspan="5" style="padding:16px 12px;color:#94a3b8;text-align:center">No appointments this month</td></tr>'}
    </tbody>
  </table>

  <p style="margin-top:32px;font-size:12px;color:#94a3b8">
    This is an automated report from MediCore. Do not reply to this email.
  </p>
</body>
</html>"""


@celery.task(name='tasks.report_tasks.send_monthly_reports', bind=True, max_retries=3)
def send_monthly_reports(self):
    """
    Scheduled task — runs on the 1st of every month at 06:00.
    Generates and emails an HTML activity report to every active doctor.
    """
    today = date.today()
    # Previous month range
    first_of_this_month = today.replace(day=1)
    last_month_last_day = first_of_this_month - timedelta(days=1)
    month_start = last_month_last_day.replace(day=1)
    month_end   = last_month_last_day
    month_label = month_start.strftime('%B %Y')

    doctors = db.session.scalars(
        sa.select(Doctor).join(User, Doctor.user_id == User.id).where(User.active == True)
    ).all()

    sent = 0
    errors = []

    for doctor in doctors:
        try:
            appointments = db.session.scalars(
                sa.select(Appointment)
                .where(
                    Appointment.doctor_id == doctor.id,
                    Appointment.date >= month_start,
                    Appointment.date <= month_end,
                )
                .options(
                    sa.orm.joinedload(Appointment.patient).joinedload(Patient.user),
                    sa.orm.joinedload(Appointment.treatment),
                )
                .order_by(Appointment.date)
            ).all()

            html_body = _build_html_report(doctor.user, doctor, appointments, month_label)

            msg = EmailMessage(
                subject=f"MediCore — Monthly Activity Report for {month_label}",
                body=html_body,
                to=[doctor.user.email],
            )
            msg.content_subtype = 'html'
            msg.send()
            sent += 1

        except Exception as exc:
            errors.append({'doctor_id': doctor.id, 'error': str(exc)})

    return {
        'month': month_label,
        'doctors_processed': len(doctors),
        'emails_sent': sent,
        'errors': errors,
    }
