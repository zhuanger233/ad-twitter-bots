from app.clients.x_client import XClient
from app.core.exceptions import XClientError


def make_client() -> XClient:
    return object.__new__(XClient)


class DummySettings:
    x_bot_username = "my_bot"


class DummyClient:
    def __init__(self, user_id: str | None) -> None:
        self.user_id = user_id

    def get_user(self, username: str):
        if self.user_id is None:
            return type("Resp", (), {"data": None})()
        data = type("Obj", (), {"data": {"id": self.user_id}})()
        return type("Resp", (), {"data": data})()


def test_extract_video_url_prefers_highest_bitrate_mp4() -> None:
    client = make_client()
    tweet = {"id": "1", "attachments": {"media_keys": ["m1"]}}
    includes = {
        "media": {
            "m1": {
                "type": "video",
                "variants": [
                    {"content_type": "application/x-mpegURL", "url": "https://example.com/master.m3u8"},
                    {"content_type": "video/mp4", "bit_rate": 256000, "url": "https://example.com/low.mp4"},
                    {"content_type": "video/mp4", "bit_rate": 832000, "url": "https://example.com/high.mp4"},
                ],
            }
        },
        "tweets": {},
    }
    assert client._extract_video_url(tweet, includes) == "https://example.com/high.mp4"


def test_find_video_source_from_quoted_tweet() -> None:
    client = make_client()
    mention = {
        "id": "10",
        "referenced_tweets": [{"id": "20", "type": "quoted"}],
    }
    includes = {
        "media": {
            "m2": {
                "type": "video",
                "variants": [
                    {"content_type": "video/mp4", "bit_rate": 512000, "url": "https://example.com/quoted.mp4"}
                ],
            }
        },
        "tweets": {
            "20": {
                "id": "20",
                "attachments": {"media_keys": ["m2"]},
            }
        },
    }
    assert client._find_video_source(mention, includes) == {
        "tweet_id": "20",
        "video_url": "https://example.com/quoted.mp4",
    }


def test_find_video_source_from_current_mention_first() -> None:
    client = make_client()
    mention = {
        "id": "10",
        "attachments": {"media_keys": ["m1"]},
        "referenced_tweets": [{"id": "20", "type": "quoted"}],
    }
    includes = {
        "media": {
            "m1": {
                "type": "video",
                "variants": [{"content_type": "video/mp4", "bit_rate": 400000, "url": "https://example.com/self.mp4"}],
            },
            "m2": {
                "type": "video",
                "variants": [{"content_type": "video/mp4", "bit_rate": 512000, "url": "https://example.com/quoted.mp4"}],
            },
        },
        "tweets": {
            "20": {
                "id": "20",
                "attachments": {"media_keys": ["m2"]},
            }
        },
    }
    assert client._find_video_source(mention, includes) == {
        "tweet_id": "10",
        "video_url": "https://example.com/self.mp4",
    }


def test_get_bot_user_id_returns_cached_value() -> None:
    client = make_client()
    client._cached_bot_user_id = "123"
    client.settings = DummySettings()
    client.client = DummyClient(user_id="999")
    assert client.get_bot_user_id() == "123"


def test_get_bot_user_id_resolves_from_username() -> None:
    client = make_client()
    client._cached_bot_user_id = None
    client.settings = DummySettings()
    client.client = DummyClient(user_id="456")
    assert client.get_bot_user_id() == "456"
    assert client._cached_bot_user_id == "456"


def test_get_bot_user_id_raises_when_username_resolution_fails() -> None:
    client = make_client()
    client._cached_bot_user_id = None
    client.settings = DummySettings()
    client.client = DummyClient(user_id=None)
    try:
        client.get_bot_user_id()
    except XClientError as exc:
        assert "resolve X bot user id" in exc.message
    else:
        raise AssertionError("Expected XClientError")


def test_resolve_video_source_falls_back_to_conversation_root() -> None:
    client = make_client()
    mention = {
        "id": "30",
        "conversation_id": "10",
        "referenced_tweets": [{"id": "20", "type": "replied_to"}],
        "includes": {
            "tweets": {"20": {"id": "20"}},
            "media": {},
        },
    }
    root = {
        "id": "10",
        "attachments": {"media_keys": ["m1"]},
        "includes": {
            "tweets": {},
            "media": {
                "m1": {
                    "type": "video",
                    "variants": [
                        {"content_type": "video/mp4", "bit_rate": 1000, "url": "https://example.com/root.mp4"}
                    ],
                }
            },
        },
    }

    def fake_fetch_tweet_details(tweet_id: str):
        return mention if tweet_id == "30" else root

    client.fetch_tweet_details = fake_fetch_tweet_details

    resolved = client.resolve_video_source("30")

    assert resolved["resolved_video_tweet_id"] == "10"
    assert resolved["video_url"] == "https://example.com/root.mp4"
