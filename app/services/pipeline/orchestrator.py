from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.clients.redis_client import get_redis_client
from app.core.constants import TaskStatus
from app.db.models.subtitle_task import SubtitleTask
from app.db.repositories.subtitle_task_repo import SubtitleTaskRepository
from app.services.pipeline.idempotency import build_dedupe_key, should_skip_duplicate
from app.workers.tasks_pipeline import run_pipeline


logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = SubtitleTaskRepository(session)
        self.redis = get_redis_client()

    def enqueue_manual(self, *, mention_tweet_id: str, video_tweet_id: str | None = None, request_user_id: str | None = None) -> SubtitleTask:
        dedupe_key = build_dedupe_key(mention_tweet_id, video_tweet_id)
        lock_key = f"lock:dedupe:{dedupe_key}"
        with self.redis.lock(lock_key, timeout=15, blocking_timeout=5):
            existing = self.repo.get_by_dedupe_key(dedupe_key)
            if existing and should_skip_duplicate(existing.status):
                logger.info(
                    "reusing existing task task_id=%s status=%s stage=%s dedupe_key=%s",
                    existing.id,
                    existing.status,
                    existing.stage,
                    dedupe_key,
                )
                if existing.status == TaskStatus.QUEUED.value:
                    run_pipeline.delay(str(existing.id))
                    logger.info("requeued queued task task_id=%s", existing.id)
                return existing
            task = self.repo.create(
                request_id=uuid.uuid4().hex,
                mention_tweet_id=mention_tweet_id,
                video_tweet_id=video_tweet_id,
                request_user_id=request_user_id,
                dedupe_key=dedupe_key,
            )
        logger.info(
            "created task task_id=%s mention_tweet_id=%s video_tweet_id=%s dedupe_key=%s",
            task.id,
            mention_tweet_id,
            video_tweet_id or "-",
            dedupe_key,
        )
        run_pipeline.delay(str(task.id))
        logger.info("dispatched pipeline task_id=%s", task.id)
        return task
