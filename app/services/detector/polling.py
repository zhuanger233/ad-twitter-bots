from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.x_client import XClient
from app.core.config import get_settings
from app.services.detector.mention_parser import parse_mention_payload
from app.services.pipeline.orchestrator import PipelineOrchestrator


class MentionPollingService:
    def __init__(self, session: Session, x_client: XClient | None = None) -> None:
        self.session = session
        self.settings = get_settings()
        self.x_client = x_client or XClient()

    def poll_once(self) -> int:
        count = 0
        mentions = self.x_client.fetch_recent_mentions(limit=self.settings.mention_lookback_limit)
        orchestrator = PipelineOrchestrator(self.session)
        for mention in mentions:
            parsed = parse_mention_payload(mention)
            if parsed is None:
                continue
            orchestrator.enqueue_manual(
                mention_tweet_id=parsed.mention_tweet_id,
                video_tweet_id=parsed.video_tweet_id,
                request_user_id=parsed.request_user_id,
            )
            count += 1
        return count
