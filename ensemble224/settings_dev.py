import os

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")

from .settings import *  # noqa: F401,F403

# Development-friendly defaults
DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
SECRET_KEY = SECRET_KEY or "dev-only-insecure-key-change-me"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Désactiver tout cache navigateur / WhiteNoise en développement local
WHITENOISE_AUTOREFRESH = True
WHITENOISE_MAX_AGE = 0
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


