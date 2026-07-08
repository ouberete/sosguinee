import logging
import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sosguinee.settings_dev")

logger = logging.getLogger(__name__)

app = Celery("sosguinee")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info("Celery debug task: %r", self.request)
