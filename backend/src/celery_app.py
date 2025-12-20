"""Celery application configuration."""

import os

from celery import Celery, signals
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "wildlife_processor",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "src.api.images.images_tasks",
        "src.api.image_pull_sources.image_pull_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

celery_app.conf.beat_schedule = {
    "pull-images-every-minute": {
        "task": "image_pull.pull_all_sources",
        "schedule": crontab(minute="*"),
        "kwargs": {"max_files_per_source": 10},
    },
}


@signals.worker_process_init.connect
def init_worker(**kwargs):
    """Initialize worker process - close and recreate database connections.

    This is critical for SQLite/SQLAlchemy to work correctly with Celery's
    prefork worker model. Without this, child processes inherit the parent's
    database connections which causes "readonly database" errors.
    """
    from src.api.database import engine

    # Dispose of the engine to close all connections inherited from parent
    engine.dispose()
