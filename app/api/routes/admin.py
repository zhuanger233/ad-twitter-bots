from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.workers.tasks_detect import enqueue_poll_mentions

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/poll-mentions")
def poll_mentions() -> dict[str, str]:
    enqueue_poll_mentions.delay()
    return {"status": "queued"}
