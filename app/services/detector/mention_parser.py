from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ParsedMention:
    mention_tweet_id: str
    video_tweet_id: str | None
    request_user_id: str | None


def parse_mention_payload(tweet: dict) -> ParsedMention | None:
    author_id = tweet.get("author_id")
    if tweet.get("ignore", False):
        return None
    return ParsedMention(
        mention_tweet_id=str(tweet["id"]),
        video_tweet_id=tweet.get("video_tweet_id"),
        request_user_id=str(author_id) if author_id else None,
    )
