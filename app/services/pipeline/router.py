from __future__ import annotations

from app.core.config import Settings
from app.core.constants import ASREngine, ErrorCode
from app.core.exceptions import VideoValidationError
from app.services.asr.models import VideoMetadata


class ASRRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def choose_engine(self, metadata: VideoMetadata) -> ASREngine:
        if not metadata.has_audio:
            raise VideoValidationError("Video has no audio stream.", code=ErrorCode.NO_AUDIO_STREAM)
        if metadata.duration_seconds > self.settings.hard_max_video_duration_seconds:
            raise VideoValidationError("Video exceeds hard max duration.", code=ErrorCode.VIDEO_TOO_LONG)
        max_size_bytes = self.settings.hard_max_filesize_mb * 1024 * 1024
        if metadata.filesize_bytes > max_size_bytes:
            raise VideoValidationError("Video exceeds hard max file size.", code=ErrorCode.VIDEO_TOO_LARGE)
        small_size_bytes = self.settings.elevenlabs_max_filesize_mb * 1024 * 1024
        if metadata.duration_seconds <= self.settings.elevenlabs_max_duration_seconds and metadata.filesize_bytes <= small_size_bytes:
            return ASREngine.ELEVENLABS
        return ASREngine.WHISPER
