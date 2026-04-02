from app.services.pipeline.idempotency import build_dedupe_key, should_skip_duplicate


def test_build_dedupe_key() -> None:
    assert build_dedupe_key("m1", "v1") == "m1:v1"
    assert build_dedupe_key("m1", None) == "m1:unknown"


def test_should_skip_duplicate() -> None:
    assert should_skip_duplicate("queued") is True
    assert should_skip_duplicate("processing") is True
    assert should_skip_duplicate("completed") is True
    assert should_skip_duplicate("failed") is False
