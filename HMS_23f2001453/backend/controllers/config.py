# controllers/config.py
import os

class Config:
    # ── Core ──────────────────────────────────────────────────────────────
    SECRET_KEY            = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
    SECURITY_PASSWORD_SALT= os.environ.get('SECURITY_PASSWORD_SALT', 'dev-salt-change-in-prod')
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'
    WTF_CSRF_ENABLED      = False
    SECURITY_REGISTERABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_USERNAME_ENABLE     = True
    SECURITY_TOKEN_MAX_AGE       = None

    # ── Database ──────────────────────────────────────────────────────────
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, '..', 'hospital.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Cache DB 1  (separate from Celery broker on DB 0)
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/1')

    # Default TTLs (seconds)
    CACHE_TTL_SHORT  = 60          # 1 min  — frequently changing data (slot counts)
    CACHE_TTL_MEDIUM = 300         # 5 min  — moderately stable (doctor list, user list)
    CACHE_TTL_LONG   = 3600        # 1 hour — rarely changing (departments, roles)

    # ── Celery ────────────────────────────────────────────────────────────
    CELERY_BROKER_URL        = os.environ.get('CELERY_BROKER_URL',  'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND    = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TIMEZONE          = 'Asia/Kolkata'   # Change to your timezone
    CELERY_ENABLE_UTC        = True

    # ── Mail (MailHog for dev, real SMTP for prod) ─────────────────────
    MAIL_SERVER   = os.environ.get('MAIL_SERVER',   'localhost')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 1025))      # MailHog SMTP port
    MAIL_USE_TLS  = os.environ.get('MAIL_USE_TLS',  'false').lower() == 'true'
    MAIL_USE_SSL  = os.environ.get('MAIL_USE_SSL',  'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None)
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@medicore.local')
