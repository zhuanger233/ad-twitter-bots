from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import TaskStage, TaskStatus
from app.db.models.subtitle_task import SubtitleTask


class SubtitleTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, request_id: str, mention_tweet_id: str, video_tweet_id: str | None, request_user_id: str | None, dedupe_key: str, priority: int = 0) -> SubtitleTask:
        task = SubtitleTask(
            request_id=request_id,
            mention_tweet_id=mention_tweet_id,
            video_tweet_id=video_tweet_id,
            request_user_id=request_user_id,
            dedupe_key=dedupe_key,
            priority=priority,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get(self, task_id: UUID) -> SubtitleTask | None:
        return self.session.get(SubtitleTask, task_id)

    def get_by_dedupe_key(self, dedupe_key: str) -> SubtitleTask | None:
        stmt = select(SubtitleTask).where(SubtitleTask.dedupe_key == dedupe_key)
        return self.session.scalar(stmt)

    def list_recent(self, limit: int = 50) -> list[SubtitleTask]:
        stmt = select(SubtitleTask).order_by(SubtitleTask.created_at.desc()).limit(limit)
        return list(self.session.scalars(stmt))

    def update_stage(self, task: SubtitleTask, *, stage: TaskStage, status: TaskStatus | None = None) -> SubtitleTask:
        task.stage = stage.value
        if status is not None:
            task.status = status.value
        if task.started_at is None and status == TaskStatus.PROCESSING:
            task.started_at = datetime.now(UTC)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def mark_failed(self, task: SubtitleTask, *, error_code: str, error_message: str) -> SubtitleTask:
        task.status = TaskStatus.FAILED.value
        task.error_code = error_code
        task.error_message = error_message
        task.completed_at = datetime.now(UTC)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def mark_completed(self, task: SubtitleTask) -> SubtitleTask:
        task.status = TaskStatus.COMPLETED.value
        task.completed_at = datetime.now(UTC)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
