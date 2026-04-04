# celery_app.py
"""
Celery application factory.

Start the worker:
    celery -A celery_app.celery worker --loglevel=info

Start the beat scheduler (for periodic tasks):
    celery -A celery_app.celery beat --loglevel=info

Monitor tasks (Flower UI at http://localhost:5555):
    celery -A celery_app.celery flower
"""
from celery import Celery
from celery.schedules import crontab


def make_celery(app):
    """
    Create and configure a Celery instance bound to a Flask app.
    All tasks run inside a Flask app context so they can access db, mail etc.
    """
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND'],
        include=['tasks.reminder_tasks', 'tasks.report_tasks', 'tasks.export_tasks'],
    )

    celery.conf.update(
        timezone=app.config.get('CELERY_TIMEZONE', 'UTC'),
        enable_utc=app.config.get('CELERY_ENABLE_UTC', True),
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        result_expires=3600,   # task results expire after 1 hour

        beat_schedule={
            # Daily appointment reminder — runs at 08:00 every day
            'daily-appointment-reminders': {
                'task': 'tasks.reminder_tasks.send_daily_reminders',
                'schedule': crontab(hour=8, minute=0),
            },
            # Monthly doctor activity report — runs at 06:00 on the 1st of every month
            'monthly-doctor-report': {
                'task': 'tasks.report_tasks.send_monthly_reports',
                'schedule': crontab(hour=6, minute=0, day_of_month=1),
            },
        },
    )

    class ContextTask(celery.Task):
        """Makes every Celery task run inside a Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
