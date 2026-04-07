from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.clients.redis_client import get_redis_client
from app.clients.x_client import XClient
from app.core.config import get_settings
from app.services.detector.mention_parser import parse_mention_payload


logger = logging.getLogger(__name__)


class MentionPollingService:
    def __init__(self, session: Session, x_client: XClient | None = None) -> None:
        self.session = session
        self.settings = get_settings()
        self.x_client = x_client or XClient()
        self.redis = get_redis_client()

    def poll_once(self, ignore_since_id: bool = False) -> int:
        since_id = None if ignore_since_id else self.get_since_id()
        logger.info("mention polling started since_id=%s", since_id or "-")
        mentions, source = self._fetch_mentions(since_id)
        if not mentions:
            logger.info("mention polling finished with no new mentions source=%s", source)
            return 0
        logger.info("mention polling fetched source=%s count=%s", source, len(mentions))

        from app.services.pipeline.orchestrator import PipelineOrchestrator

        orchestrator = PipelineOrchestrator(self.session)
        count = 0
        max_seen_id = since_id
        for mention in mentions:
            mention_id = str(mention["id"])
            max_seen_id = self._max_tweet_id(max_seen_id, mention_id)
            parsed = parse_mention_payload(mention)
            if parsed is None:
                logger.info("mention skipped mention_tweet_id=%s reason=parse_none", mention_id)
                continue
            logger.info(
                "mention detected mention_tweet_id=%s video_tweet_id=%s request_user_id=%s",
                parsed.mention_tweet_id,
                parsed.video_tweet_id or "-",
                parsed.request_user_id or "-",
            )
            orchestrator.enqueue_manual(
                mention_tweet_id=parsed.mention_tweet_id,
                video_tweet_id=parsed.video_tweet_id,
                request_user_id=parsed.request_user_id,
            )
            count += 1

        if max_seen_id is not None:
            self._set_since_id(max_seen_id)
        logger.info("mention polling finished enqueued=%s new_since_id=%s", count, max_seen_id or since_id or "-")
        return count


    def preview_once(self, ignore_since_id: bool = False) -> dict[str, object]:
        since_id = None if ignore_since_id else self.get_since_id()
        mentions, source = self._fetch_mentions(since_id)
        items: list[dict[str, str | None]] = []
        for mention in mentions:
            parsed = parse_mention_payload(mention)
            items.append(
                {
                    "mention_tweet_id": str(mention.get("id")),
                    "author_id": str(mention.get("author_id")) if mention.get("author_id") else None,
                    "conversation_id": str(mention.get("conversation_id")) if mention.get("conversation_id") else None,
                    "video_tweet_id": str(mention.get("video_tweet_id")) if mention.get("video_tweet_id") else None,
                    "parsed": "true" if parsed else "false",
                }
            )
        return {
            "cursor_key": self.cursor_key,
            "since_id": since_id,
            "ignore_since_id": ignore_since_id,
            "source": source,
            "x_meta": getattr(self.x_client, "last_mentions_meta", None),
            "count": len(items),
            "mentions": items,
        }


    def _fetch_mentions(self, since_id: str | None) -> tuple[list[dict], str]:
        mentions = self.x_client.fetch_recent_mentions(
            limit=self.settings.mention_lookback_limit,
            since_id=since_id,
        )
        if mentions:
            return mentions, "mentions_timeline"
        logger.info("mentions timeline returned empty, trying recent search fallback")
        mentions = self.x_client.search_recent_mentions(
            limit=self.settings.mention_lookback_limit,
            since_id=since_id,
        )
        return mentions, "recent_search"

    def get_since_id(self) -> str | None:
        value = self.redis.get(self.cursor_key)
        return str(value) if value else None

    def reset_since_id(self) -> bool:
        deleted = self.redis.delete(self.cursor_key)
        logger.info("mention polling cursor reset key=%s deleted=%s", self.cursor_key, deleted)
        return bool(deleted)

    def _set_since_id(self, since_id: str) -> None:
        self.redis.set(self.cursor_key, since_id)

    @property
    def cursor_key(self) -> str:
        bot_user_id = self.x_client.get_bot_user_id()
        return f"x:mentions:since_id:{bot_user_id}"

    @staticmethod
    def _max_tweet_id(current: str | None, candidate: str) -> str:
        if current is None:
            return candidate
        return candidate if int(candidate) > int(current) else current
