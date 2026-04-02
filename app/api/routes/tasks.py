from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.repositories.subtitle_task_repo import SubtitleTaskRepository
from app.services.pipeline.orchestrator import PipelineOrchestrator

router = APIRouter(prefix="/tasks", tags=["tasks"])


class ProcessTaskRequest(BaseModel):
    mention_tweet_id: str
    video_tweet_id: str | None = None
    request_user_id: str | None = None


class TaskResponse(BaseModel):
    id: str
    request_id: str
    status: str
    stage: str
    mention_tweet_id: str
    video_tweet_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


@router.post("/process", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
def process_task(payload: ProcessTaskRequest, db: Session = Depends(get_db)) -> TaskResponse:
    orchestrator = PipelineOrchestrator(db)
    task = orchestrator.enqueue_manual(
        mention_tweet_id=payload.mention_tweet_id,
        video_tweet_id=payload.video_tweet_id,
        request_user_id=payload.request_user_id,
    )
    return TaskResponse.model_validate(task, from_attributes=True)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, db: Session = Depends(get_db)) -> TaskResponse:
    repo = SubtitleTaskRepository(db)
    task = repo.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse.model_validate(task, from_attributes=True)


@router.get("", response_model=list[TaskResponse])
def list_tasks(limit: int = 50, db: Session = Depends(get_db)) -> list[TaskResponse]:
    repo = SubtitleTaskRepository(db)
    return [TaskResponse.model_validate(task, from_attributes=True) for task in repo.list_recent(limit=limit)]
