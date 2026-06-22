from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "turf_saas",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_default_queue="default",
    task_routes={
        "app.tasks.whatsapp_tasks.*": {"queue": "whatsapp"},
        "app.tasks.payout_tasks.*": {"queue": "payouts"},
        "app.tasks.refund_tasks.*": {"queue": "refunds"},
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
