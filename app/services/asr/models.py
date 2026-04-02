from __future__ import annotations

from pydantic import BaseModel


class WordTimestamp(BaseModel):
    text: str
    start: float
    end: float


class Segment(BaseModel):
    text: str
    start: float
    end: float
    words: list[WordTimestamp] | None = None


class TranscriptionResult(BaseModel):
    language: str | None = None
    duration: float | None = None
    segments: list[Segment]
    raw_response: dict | None = None


class VideoMetadata(BaseModel):
    duration_seconds: float
    filesize_bytes: int
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    has_audio: bool = True
    audio_codec: str | None = None
    video_codec: str | None = None
