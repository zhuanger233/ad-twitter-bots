from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.redis_client import get_redis_client
from app.clients.x_client import XClient
from app.core.config import get_settings
from app.services.detector.mention_parser import parse_mention_payload


class MentionPollingService:
    def __init__(self, session: Session, x_client: XClient | None = None) -> None:
        self.session = session
        self.settings = get_settings()
        self.x_client = x_client or XClient()
        self.redis = get_redis_client()

    def poll_once(self) -> int:
        since_id = self._get_since_id()
        mentions = self.x_client.fetch_recent_mentions(
            limit=self.settings.mention_lookback_limit,
            since_id=since_id,
        )
        if not mentions:
            return 0

        from app.services.pipeline.orchestrator import PipelineOrchestrator

        orchestrator = PipelineOrchestrator(self.session)
        count = 0
        max_seen_id = since_id
        for mention in mentions:
            mention_id = str(mention["id"])
            max_seen_id = self._max_tweet_id(max_seen_id, mention_id)
            parsed = parse_mention_payload(mention)
            if parsed is None:
                continue
            orchestrator.enqueue_manual(
                mention_tweet_id=parsed.mention_tweet_id,
                video_tweet_id=parsed.video_tweet_id,
                request_user_id=parsed.request_user_id,
            )
            count += 1

        if max_seen_id is not None:
            self._set_since_id(max_seen_id)
        return count

    def _get_since_id(self) -> str | None:
        value = self.redis.get(self._cursor_key)
        return str(value) if value else None

    def _set_since_id(self, since_id: str) -> None:
        self.redis.set(self._cursor_key, since_id)

    @property
    def _cursor_key(self) -> str:
        bot_user_id = self.x_client.get_bot_user_id()
        return f"x:mentions:since_id:{bot_user_id}"

    @staticmethod
    def _max_tweet_id(current: str | None, candidate: str) -> str:
        if current is None:
            return candidate
        return candidate if int(candidate) > int(current) else current
