"""
Celery application for FrameAI background tasks.

Start a worker:
  celery -A celery_app worker --loglevel=info

Start beat scheduler (periodic tasks):
  celery -A celery_app beat --loglevel=info

Combined (dev only):
  celery -A celery_app worker --beat --loglevel=info
"""
from celery import Celery
from celery.schedules import crontab

from config import settings

celery_app = Celery(
    "frameai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.generate", "tasks.price_refresh"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    result_expires=86400,           # 24h — matches R2 image TTL
    task_track_started=True,
    worker_prefetch_multiplier=1,   # one task per worker (generation is API-heavy)
    beat_schedule={
        "refresh-prices-weekly": {
            "task": "tasks.price_refresh.refresh_prices",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3am IST
        },
    },
)
