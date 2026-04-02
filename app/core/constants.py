from enum import StrEnum


class TaskStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    IGNORED = "ignored"


class TaskStage(StrEnum):
    DETECTED = "detected"
    RESOLVED_VIDEO = "resolved_video"
    DOWNLOADED = "downloaded"
    INSPECTED = "inspected"
    TRANSCRIBING = "transcribing"
    SUBTITLE_GENERATED = "subtitle_generated"
    BURNED = "burned"
    UPLOADED_BACKUP = "uploaded_backup"
    UPLOADED_X = "uploaded_x"
    REPLIED = "replied"
    CLEANED_UP = "cleaned_up"


class ASREngine(StrEnum):
    ELEVENLABS = "elevenlabs"
    WHISPER = "whisper"


class ErrorCode(StrEnum):
    NO_VIDEO_FOUND = "NO_VIDEO_FOUND"
    VIDEO_DOWNLOAD_FAILED = "VIDEO_DOWNLOAD_FAILED"
    VIDEO_TOO_LARGE = "VIDEO_TOO_LARGE"
    VIDEO_TOO_LONG = "VIDEO_TOO_LONG"
    NO_AUDIO_STREAM = "NO_AUDIO_STREAM"
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    SUBTITLE_GENERATION_FAILED = "SUBTITLE_GENERATION_FAILED"
    FFMPEG_FAILED = "FFMPEG_FAILED"
    X_MEDIA_UPLOAD_FAILED = "X_MEDIA_UPLOAD_FAILED"
    X_REPLY_FAILED = "X_REPLY_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
