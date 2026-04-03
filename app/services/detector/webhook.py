from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings


@dataclass(slots=True)
class WebhookMentionEvent:
    mention_tweet_id: str
    request_user_id: str | None
    video_tweet_id: str | None = None


class XWebhookService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_crc_response(self, crc_token: str) -> dict[str, str]:
        digest = hmac.new(
            self.settings.x_api_secret.encode("utf-8"),
            crc_token.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        response_token = "sha256=" + base64.b64encode(digest).decode("utf-8")
        return {"response_token": response_token}

    def validate_signature(self, body: bytes, signature: str | None) -> bool:
        if not self.settings.x_webhook_validation_enabled:
            return True
        if not signature:
            return False
        digest = hmac.new(
            self.settings.x_api_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).digest()
        expected = "sha256=" + base64.b64encode(digest).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    def parse_mentions(self, payload: dict[str, Any]) -> list[WebhookMentionEvent]:
        bot_username = self.settings.x_bot_username.lstrip("@").lower().strip()
        bot_user_id = self.settings.x_bot_user_id.strip() if self.settings.x_bot_user_id else None
        users = payload.get("users", {})
        events = payload.get("tweet_create_events", []) or []
        mentions: list[WebhookMentionEvent] = []

        for event in events:
            author_id = str(event.get("user", {}).get("id_str") or event.get("user", {}).get("id") or "")
            if bot_user_id and author_id == bot_user_id:
                continue

            if not self._event_mentions_bot(event, bot_username, bot_user_id):
                continue

            mention_tweet_id = str(event.get("id_str") or event.get("id") or "")
            if not mention_tweet_id:
                continue

            video_tweet_id = self._extract_candidate_video_tweet_id(event, users)
            mentions.append(
                WebhookMentionEvent(
                    mention_tweet_id=mention_tweet_id,
                    request_user_id=author_id or None,
                    video_tweet_id=video_tweet_id,
                )
            )
        return mentions

    def parse_body(self, body: bytes) -> dict[str, Any]:
        return json.loads(body.decode("utf-8"))

    def _event_mentions_bot(self, event: dict[str, Any], bot_username: str, bot_user_id: str | None) -> bool:
        entities = event.get("entities", {}) or {}
        user_mentions = entities.get("user_mentions", []) or []
        for mention in user_mentions:
            mention_screen_name = str(mention.get("screen_name") or "").lower()
            mention_id = str(mention.get("id_str") or mention.get("id") or "")
            if bot_username and mention_screen_name == bot_username:
                return True
            if bot_user_id and mention_id == bot_user_id:
                return True
        return False

    def _extract_candidate_video_tweet_id(self, event: dict[str, Any], users: dict[str, Any]) -> str | None:
        in_reply_to = event.get("in_reply_to_status_id_str") or event.get("in_reply_to_status_id")
        quoted_status_id = event.get("quoted_status_id_str") or event.get("quoted_status_id")
        candidate = quoted_status_id or in_reply_to
        return str(candidate) if candidate else None
