try:
    from .celery import app as celery_app
except Exception:  # pragma: no cover - keep Django boot resilient when Celery isn't installed.
    celery_app = None

__all__ = ("celery_app",)
