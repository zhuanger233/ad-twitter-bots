from __future__ import annotations

from app.core.constants import ErrorCode


class AppError(Exception):
    def __init__(self, message: str, *, code: ErrorCode = ErrorCode.INTERNAL_ERROR, retryable: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable


class NoVideoFoundError(AppError):
    def __init__(self, message: str = "No video found for mention.") -> None:
        super().__init__(message, code=ErrorCode.NO_VIDEO_FOUND)


class VideoValidationError(AppError):
    pass


class TranscriptionError(AppError):
    def __init__(self, message: str, retryable: bool = True) -> None:
        super().__init__(message, code=ErrorCode.TRANSCRIPTION_FAILED, retryable=retryable)


class FFmpegError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=ErrorCode.FFMPEG_FAILED)


class XClientError(AppError):
    def __init__(self, message: str, code: ErrorCode, retryable: bool = True) -> None:
        super().__init__(message, code=code, retryable=retryable)
