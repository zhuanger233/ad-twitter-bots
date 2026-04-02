from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.clients.redis_client import get_redis_client
from app.db.models.subtitle_task import SubtitleTask
from app.db.repositories.subtitle_task_repo import SubtitleTaskRepository
from app.services.pipeline.idempotency import build_dedupe_key, should_skip_duplicate
from app.workers.tasks_pipeline import run_pipeline


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
                return existing
            task = self.repo.create(
                request_id=uuid.uuid4().hex,
                mention_tweet_id=mention_tweet_id,
                video_tweet_id=video_tweet_id,
                request_user_id=request_user_id,
                dedupe_key=dedupe_key,
            )
        run_pipeline.delay(str(task.id))
        return task
