"""Celery app for background monitoring and report jobs."""
from celery import Celery
from backend.config import get_settings

settings = get_settings()
app = Celery(
    "network_monitoring",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
    include=[
        "backend.tasks.monitoring",
        "backend.tasks.reports",
    ],
)
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "backend.tasks.monitoring.*": {"queue": "monitoring"},
        "backend.tasks.reports.*": {"queue": "reports"},
    },
)
app.conf.beat_schedule = {
    "daily-report": {
        "task": "backend.tasks.reports.generate_daily_report_task",
        "schedule": 60 * 60 * 24,  # every 24h
    },
}
