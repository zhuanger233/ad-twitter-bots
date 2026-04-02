from pathlib import Path

from app.services.reply.tweet_replier import TweetReplier


class FakeXClient:
    def upload_video(self, video_path: Path) -> str:
        return "mid_1"

    def reply_with_media(self, mention_tweet_id: str, text: str, media_id: str) -> str:
        assert mention_tweet_id == "mention_1"
        assert media_id == "mid_1"
        return "reply_1"


def test_reply_flow() -> None:
    media_id, reply_id = TweetReplier(x_client=FakeXClient()).upload_and_reply(
        mention_tweet_id="mention_1",
        output_video_path=Path("video.mp4"),
        text="done",
    )
    assert media_id == "mid_1"
    assert reply_id == "reply_1"
