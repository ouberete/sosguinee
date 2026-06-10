import os

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")

from .settings import *  # noqa: F401,F403

# Development-friendly defaults
SECRET_KEY = SECRET_KEY or "dev-only-insecure-key-change-me"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
