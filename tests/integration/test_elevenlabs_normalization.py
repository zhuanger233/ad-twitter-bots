from pathlib import Path

from app.services.asr.elevenlabs_provider import ElevenLabsASRProvider


class FakeClient:
    def transcribe(self, media_path: Path) -> dict:
        return {
            "language_code": "en",
            "duration_seconds": 2.0,
            "words": [
                {"text": "hello", "start": 0.0, "end": 0.5},
                {"text": "world", "start": 0.6, "end": 1.0},
            ],
        }


def test_elevenlabs_normalization_from_words(tmp_path: Path) -> None:
    provider = ElevenLabsASRProvider(client=FakeClient())
    result = provider.transcribe(tmp_path / "sample.mp4")
    assert result.language == "en"
    assert result.segments[0].text == "hello world"
