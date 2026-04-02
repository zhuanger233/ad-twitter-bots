from __future__ import annotations

from app.core.constants import TaskStatus


def build_dedupe_key(mention_tweet_id: str, video_tweet_id: str | None) -> str:
    return f"{mention_tweet_id}:{video_tweet_id or 'unknown'}"


def should_skip_duplicate(existing_status: str) -> bool:
    return existing_status in {TaskStatus.QUEUED.value, TaskStatus.PROCESSING.value, TaskStatus.COMPLETED.value}
