import logging
import os

from celery import Celery


# En prod DJANGO_SETTINGS_MODULE doit être défini explicitement dans l'env.
# On se rabat sur le fichier de base (qui lit ENVIRONMENT depuis l'env)
# plutôt que sur settings_dev pour éviter les fuites de config.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ensemble224.settings")

logger = logging.getLogger(__name__)

app = Celery("ensemble224")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info("Celery debug task: %r", self.request)
