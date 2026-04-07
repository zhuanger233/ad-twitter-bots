from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.services.detector.polling import MentionPollingService
from app.workers.tasks_detect import enqueue_poll_mentions

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/poll-mentions")
def poll_mentions(ignore_since_id: bool = False, reset_cursor: bool = False) -> dict[str, str | bool]:
    enqueue_poll_mentions.delay(ignore_since_id=ignore_since_id, reset_cursor=reset_cursor)
    return {"status": "queued", "ignore_since_id": ignore_since_id, "reset_cursor": reset_cursor}


@router.get("/poll-mentions/preview")
def preview_mentions(ignore_since_id: bool = False, db: Session = Depends(get_db)) -> dict[str, object]:
    service = MentionPollingService(db)
    return service.preview_once(ignore_since_id=ignore_since_id)


@router.get("/poll-mentions/cursor")
def get_mentions_cursor(db: Session = Depends(get_db)) -> dict[str, str | None]:
    service = MentionPollingService(db)
    return {"cursor_key": service.cursor_key, "since_id": service.get_since_id()}


@router.delete("/poll-mentions/cursor")
def reset_mentions_cursor(db: Session = Depends(get_db)) -> dict[str, str | bool | None]:
    service = MentionPollingService(db)
    cursor_key = service.cursor_key
    old_since_id = service.get_since_id()
    deleted = service.reset_since_id()
    return {"cursor_key": cursor_key, "old_since_id": old_since_id, "deleted": deleted}
