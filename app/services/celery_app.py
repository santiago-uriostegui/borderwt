import os

from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "borderwt",
    broker=broker_url,
    backend=result_backend,
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
            "args": ("scheduled",),
        },
    },
)

# Imported after celery_app is configured, since borderwt.py needs it to
# register the task; also re-exports import_border_wait_times for callers.
from app.services.borderwt import import_border_wait_times  # noqa: E402,F401
