from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_settings_dep
from app.core.config import Settings
from app.services.detector.webhook import XWebhookService
from app.services.pipeline.orchestrator import PipelineOrchestrator

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("/x")
async def x_webhook_crc(
    crc_token: str,
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, str]:
    service = XWebhookService(settings)
    return service.build_crc_response(crc_token)


@router.post("/x")
async def x_webhook_event(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, int | str]:
    body = await request.body()
    signature = request.headers.get("x-twitter-webhooks-signature")
    service = XWebhookService(settings)
    if not service.validate_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    payload = service.parse_body(body)
    mentions = service.parse_mentions(payload)
    orchestrator = PipelineOrchestrator(db)
    enqueued = 0
    for mention in mentions:
        orchestrator.enqueue_manual(
            mention_tweet_id=mention.mention_tweet_id,
            video_tweet_id=mention.video_tweet_id,
            request_user_id=mention.request_user_id,
        )
        enqueued += 1
    return {"status": "accepted", "enqueued": enqueued}
