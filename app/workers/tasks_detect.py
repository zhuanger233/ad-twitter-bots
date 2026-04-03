from __future__ import annotations

import logging

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.detector.polling import MentionPollingService
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks_detect.enqueue_poll_mentions")
def enqueue_poll_mentions() -> int:
    settings = get_settings()
    if not settings.mention_polling_enabled:
        logger.info("mention polling skipped because MENTION_POLLING_ENABLED=false")
        return 0
    logger.info("enqueue_poll_mentions started interval_seconds=%s lookback_limit=%s", settings.mention_poll_interval_seconds, settings.mention_lookback_limit)
    with SessionLocal() as session:
        service = MentionPollingService(session)
        count = service.poll_once()
        logger.info("enqueue_poll_mentions finished enqueued=%s", count)
        return count
