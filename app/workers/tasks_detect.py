from __future__ import annotations

import logging

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.detector.polling import MentionPollingService
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks_detect.enqueue_poll_mentions")
def enqueue_poll_mentions(ignore_since_id: bool = False, reset_cursor: bool = False) -> int:
    settings = get_settings()
    if not settings.mention_polling_enabled:
        logger.info("mention polling skipped because MENTION_POLLING_ENABLED=false")
        return 0
    logger.info("enqueue_poll_mentions started interval_seconds=%s lookback_limit=%s ignore_since_id=%s reset_cursor=%s", settings.mention_poll_interval_seconds, settings.mention_lookback_limit, ignore_since_id, reset_cursor)
    with SessionLocal() as session:
        service = MentionPollingService(session)
        if reset_cursor:
            service.reset_since_id()
        count = service.poll_once(ignore_since_id=ignore_since_id)
        logger.info("enqueue_poll_mentions finished enqueued=%s", count)
        return count
