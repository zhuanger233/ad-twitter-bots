from app.core.config import Settings
from app.core.constants import ASREngine
from app.core.exceptions import VideoValidationError
from app.services.asr.models import VideoMetadata
from app.services.pipeline.router import ASRRouter


def make_settings() -> Settings:
    return Settings(
        hard_max_video_duration_seconds=600,
        hard_max_filesize_mb=100,
        elevenlabs_max_duration_seconds=120,
        elevenlabs_max_filesize_mb=20,
    )


def test_router_chooses_elevenlabs_for_small_media() -> None:
    router = ASRRouter(make_settings())
    metadata = VideoMetadata(duration_seconds=60, filesize_bytes=10 * 1024 * 1024, has_audio=True)
    assert router.choose_engine(metadata) == ASREngine.ELEVENLABS


def test_router_chooses_whisper_for_large_media() -> None:
    router = ASRRouter(make_settings())
    metadata = VideoMetadata(duration_seconds=180, filesize_bytes=30 * 1024 * 1024, has_audio=True)
    assert router.choose_engine(metadata) == ASREngine.WHISPER


def test_router_rejects_no_audio() -> None:
    router = ASRRouter(make_settings())
    metadata = VideoMetadata(duration_seconds=30, filesize_bytes=1024, has_audio=False)
    try:
        router.choose_engine(metadata)
    except VideoValidationError as exc:
        assert exc.code.value == "NO_AUDIO_STREAM"
    else:
        raise AssertionError("Expected VideoValidationError")
