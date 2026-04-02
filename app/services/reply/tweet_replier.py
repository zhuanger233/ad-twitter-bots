from __future__ import annotations

from pathlib import Path

from app.clients.x_client import XClient


class TweetReplier:
    def __init__(self, x_client: XClient | None = None) -> None:
        self.x_client = x_client or XClient()

    def upload_and_reply(self, *, mention_tweet_id: str, output_video_path: Path, text: str) -> tuple[str, str]:
        media_id = self.x_client.upload_video(output_video_path)
        reply_tweet_id = self.x_client.reply_with_media(mention_tweet_id=mention_tweet_id, text=text, media_id=media_id)
        return media_id, reply_tweet_id
