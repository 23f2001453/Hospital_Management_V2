# app.py
import uuid
from flask import Flask
from flask_security import Security
from flask_restful import Api
from flask_mailman import Mail
from flask_cors import CORS

from controllers.database import db
from controllers.models import User, Role
from controllers.user_datastore import user_datastore

from controllers.authentication_apis import (
    RegisterAPI, LoginAPI, LogoutAPI, MeAPI,
    UpdateProfileAPI, AdminUserListAPI, AdminUserDetailAPI,
)
from controllers.appointment_apis import (
    DoctorListAPI, DoctorAvailabilityListAPI,
    ManageAvailabilityAPI, ManageAvailabilityDetailAPI,
    DoctorAppointmentsAPI, DoctorUpdateAppointmentStatusAPI,
    DoctorPatientListAPI, BookSlotAPI,
    PatientAppointmentsAPI, PatientCancelAppointmentAPI,
)
from controllers.treatment_apis import (
    TreatAppointmentAPI, PatientViewTreatmentAPI, PatientTreatmentHistoryAPI,
)
from controllers.admin_apis import (
    AdminSearchAPI, AdminAppointmentsAPI, AdminTreatmentDetailAPI,
    AdminBlacklistAPI, AdminJobStatusAPI, PatientExportCSVAPI,
    register_admin_routes,
)

mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object('controllers.config.Config')

    db.init_app(app)
    CORS(app)
    mail.init_app(app)
    security = Security(app, user_datastore)

    api = Api(app, prefix='/api')

    # ── Auth ──────────────────────────────────────────────────────────────
    api.add_resource(RegisterAPI,        '/auth/register')
    api.add_resource(LoginAPI,           '/auth/login')
    api.add_resource(LogoutAPI,          '/auth/logout')
    api.add_resource(MeAPI,              '/auth/me')
    api.add_resource(UpdateProfileAPI,   '/auth/profile')
    api.add_resource(AdminUserListAPI,   '/admin/users')
    api.add_resource(AdminUserDetailAPI, '/admin/users/<int:user_id>')

    # ── Doctors & availability ─────────────────────────────────────────────
    api.add_resource(DoctorListAPI,                    '/doctors')
    api.add_resource(DoctorAvailabilityListAPI,        '/doctors/<int:doctor_id>/availability')
    api.add_resource(ManageAvailabilityAPI,            '/doctor/availability')
    api.add_resource(ManageAvailabilityDetailAPI,      '/doctor/availability/<int:slot_id>')

    # ── Doctor appointment management ─────────────────────────────────────
    api.add_resource(DoctorAppointmentsAPI,            '/doctor/appointments')
    api.add_resource(DoctorUpdateAppointmentStatusAPI, '/doctor/appointments/<int:appointment_id>/status')
    api.add_resource(DoctorPatientListAPI,             '/doctor/patients')

    # ── Treatment ─────────────────────────────────────────────────────────
    api.add_resource(TreatAppointmentAPI,        '/doctor/appointments/<int:appointment_id>/treat')
    api.add_resource(PatientTreatmentHistoryAPI, '/doctor/patients/<int:patient_id>/history')

    # ── Patient actions ───────────────────────────────────────────────────
    api.add_resource(BookSlotAPI,                '/appointments/book/<int:slot_id>')
    api.add_resource(PatientAppointmentsAPI,     '/appointments/my')
    api.add_resource(PatientCancelAppointmentAPI,'/appointments/<int:appointment_id>/cancel')
    api.add_resource(PatientViewTreatmentAPI,    '/appointments/<int:appointment_id>/treatment')

    # ── Admin extended + jobs + export ────────────────────────────────────
    register_admin_routes(api)

    # ── DB seed ───────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

        for role_name, desc in [('admin', 'Administrator'), ('doctor', 'Doctor'), ('patient', 'Patient')]:
            user_datastore.find_or_create_role(name=role_name, description=desc)

        if not user_datastore.find_user(email='admin@example.com'):
            admin_user = user_datastore.create_user(
                username='admin', email='admin@example.com', password='admin123',
                fs_uniquifier=str(uuid.uuid4()), fs_token_uniquifier=str(uuid.uuid4()),
            )
            user_datastore.add_role_to_user(admin_user, 'admin')

        if not user_datastore.find_user(email='doctor@example.com'):
            from controllers.models import Doctor
            doctor_user = user_datastore.create_user(
                username='doctor', email='doctor@example.com', password='doctor123',
                fs_uniquifier=str(uuid.uuid4()), fs_token_uniquifier=str(uuid.uuid4()),
            )
            user_datastore.add_role_to_user(doctor_user, 'doctor')
            db.session.flush()
            db.session.add(Doctor(user_id=doctor_user.id, specialization='General Practice', experience_years=5))

        if not user_datastore.find_user(email='patient@example.com'):
            from controllers.models import Patient
            patient_user = user_datastore.create_user(
                username='patient', email='patient@example.com', password='patient123',
                fs_uniquifier=str(uuid.uuid4()), fs_token_uniquifier=str(uuid.uuid4()),
            )
            user_datastore.add_role_to_user(patient_user, 'patient')
            db.session.flush()
            db.session.add(Patient(user_id=patient_user.id, emergency_contact='9999999999'))

        db.session.commit()

    return app


app = create_app()

# Celery must be created after app is ready
from celery_app import make_celery
celery = make_celery(app)


@app.route('/')
def index():
    return {
        'message': 'MediCore API',
        'version': '2.0',
        'endpoints': {
            'auth':        '/api/auth/...',
            'admin':       '/api/admin/...',
            'appointments':'/api/appointments/...',
            'jobs':        '/api/jobs/<task_id>',
        }
    }, 200


if __name__ == '__main__':
    app.run(debug=True)
