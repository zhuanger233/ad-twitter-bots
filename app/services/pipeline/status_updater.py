from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import TaskStage, TaskStatus
from app.db.models.subtitle_task import SubtitleTask
from app.db.repositories.subtitle_task_repo import SubtitleTaskRepository


class StatusUpdater:
    def __init__(self, session: Session) -> None:
        self.repo = SubtitleTaskRepository(session)

    def advance(self, task: SubtitleTask, stage: TaskStage, status: TaskStatus | None = None) -> SubtitleTask:
        return self.repo.update_stage(task, stage=stage, status=status)
