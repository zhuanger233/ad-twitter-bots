import sys
from types import SimpleNamespace

from app.services.detector.polling import MentionPollingService


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value


class FakeXClient:
    def __init__(self, mentions: list[dict], bot_user_id: str = "42") -> None:
        self.mentions = mentions
        self.bot_user_id = bot_user_id
        self.calls: list[tuple[int, str | None]] = []

    def get_bot_user_id(self) -> str:
        return self.bot_user_id

    def fetch_recent_mentions(self, limit: int, since_id: str | None = None) -> list[dict]:
        self.calls.append((limit, since_id))
        return list(self.mentions)


class FakeOrchestrator:
    def __init__(self, session: object) -> None:
        self.session = session
        self.calls: list[dict[str, str | None]] = []

    def enqueue_manual(self, *, mention_tweet_id: str, video_tweet_id: str | None = None, request_user_id: str | None = None):
        self.calls.append(
            {
                "mention_tweet_id": mention_tweet_id,
                "video_tweet_id": video_tweet_id,
                "request_user_id": request_user_id,
            }
        )


def test_poll_once_uses_since_id_and_updates_cursor(monkeypatch) -> None:
    fake_redis = FakeRedis()
    fake_redis.set("x:mentions:since_id:42", "100")
    fake_x_client = FakeXClient(
        mentions=[
            {"id": "101", "author_id": "u1", "video_tweet_id": "501"},
            {"id": "109", "author_id": "u2", "video_tweet_id": None},
        ]
    )
    fake_orchestrator = FakeOrchestrator(session=object())

    monkeypatch.setattr("app.services.detector.polling.get_settings", lambda: SimpleNamespace(mention_lookback_limit=20))
    monkeypatch.setattr("app.services.detector.polling.get_redis_client", lambda: fake_redis)
    monkeypatch.setitem(sys.modules, "app.services.pipeline.orchestrator", SimpleNamespace(PipelineOrchestrator=lambda session: fake_orchestrator))

    service = MentionPollingService(session=object(), x_client=fake_x_client)

    count = service.poll_once()

    assert count == 2
    assert fake_x_client.calls == [(20, "100")]
    assert fake_redis.get("x:mentions:since_id:42") == "109"
    assert fake_orchestrator.calls == [
        {"mention_tweet_id": "101", "video_tweet_id": "501", "request_user_id": "u1"},
        {"mention_tweet_id": "109", "video_tweet_id": None, "request_user_id": "u2"},
    ]


def test_poll_once_returns_zero_when_no_new_mentions(monkeypatch) -> None:
    fake_redis = FakeRedis()
    fake_x_client = FakeXClient(mentions=[])
    fake_orchestrator = FakeOrchestrator(session=object())

    monkeypatch.setattr("app.services.detector.polling.get_settings", lambda: SimpleNamespace(mention_lookback_limit=20))
    monkeypatch.setattr("app.services.detector.polling.get_redis_client", lambda: fake_redis)
    monkeypatch.setitem(sys.modules, "app.services.pipeline.orchestrator", SimpleNamespace(PipelineOrchestrator=lambda session: fake_orchestrator))

    service = MentionPollingService(session=object(), x_client=fake_x_client)

    count = service.poll_once()

    assert count == 0
    assert fake_x_client.calls == [(20, None)]
    assert fake_redis.values == {}
    assert fake_orchestrator.calls == []
