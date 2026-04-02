# controllers/config.py
import os

class Config:
    # ── Core ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')

    # ── Database ──────────────────────────────────────────────────────────
    # SQLite for local dev. Swap the URI for PostgreSQL/MySQL in production.
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, '..', 'hospital.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Flask-Security-Too ────────────────────────────────────────────────
    SECURITY_PASSWORD_SALT       = os.environ.get('SECURITY_PASSWORD_SALT', 'change-salt-too')
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'

    # Token-based auth (no session cookies needed for a REST API)
    WTF_CSRF_ENABLED             = False        # disable CSRF for pure API
    SECURITY_TOKEN_MAX_AGE       = None         # tokens don't expire (set seconds if you want expiry)

    # Required for Flask-Security token auth to work
    SECURITY_TRACKABLE           = False
    SECURITY_REGISTERABLE        = False        # we handle registration ourselves
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_USERNAME_ENABLE     = True         # allow username field on User model
