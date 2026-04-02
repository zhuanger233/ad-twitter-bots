from __future__ import annotations

from app.db.session import SessionLocal
from app.services.detector.polling import MentionPollingService
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks_detect.enqueue_poll_mentions")
def enqueue_poll_mentions() -> int:
    with SessionLocal() as session:
        service = MentionPollingService(session)
        return service.poll_once()
