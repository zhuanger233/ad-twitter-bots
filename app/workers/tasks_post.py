from __future__ import annotations

from pathlib import Path

from app.services.reply.tweet_replier import TweetReplier
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks_post.upload_and_reply")
def upload_and_reply(mention_tweet_id: str, output_video_path: str, text: str) -> dict[str, str]:
    replier = TweetReplier()
    media_id, reply_tweet_id = replier.upload_and_reply(
        mention_tweet_id=mention_tweet_id,
        output_video_path=Path(output_video_path),
        text=text,
    )
    return {"media_id": media_id, "reply_tweet_id": reply_tweet_id}
