from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "subtitle_bot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks_detect",
        "app.workers.tasks_pipeline",
        "app.workers.tasks_asr",
        "app.workers.tasks_ffmpeg",
        "app.workers.tasks_post",
    ],
)

celery_app.conf.task_routes = {
    "app.workers.tasks_detect.*": {"queue": "queue_mentions"},
    "app.workers.tasks_pipeline.run_pipeline": {"queue": "queue_io"},
    "app.workers.tasks_pipeline.resolve_video": {"queue": "queue_io"},
    "app.workers.tasks_pipeline.download_video": {"queue": "queue_io"},
    "app.workers.tasks_pipeline.inspect_video": {"queue": "queue_io"},
    "app.workers.tasks_asr.*": {"queue": "queue_asr"},
    "app.workers.tasks_ffmpeg.*": {"queue": "queue_ffmpeg"},
    "app.workers.tasks_post.*": {"queue": "queue_post"},
}

if settings.mention_polling_enabled:
    celery_app.conf.beat_schedule = {
        "poll-x-mentions": {
            "task": "app.workers.tasks_detect.enqueue_poll_mentions",
            "schedule": float(settings.mention_poll_interval_seconds),
        }
    }
else:
    celery_app.conf.beat_schedule = {}
