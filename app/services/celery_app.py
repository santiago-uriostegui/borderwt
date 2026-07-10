from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "borderwt",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sample-task-every-hour": {
            "task": "app.services.celery_app.import_border_wait_times",
            "schedule": 5 * 60,
        },
    },
)

# Imported after celery_app is configured, since borderwt.py needs it to
# register the task; also re-exports import_border_wait_times for callers.
from app.services.borderwt import import_border_wait_times  # noqa: E402,F401
