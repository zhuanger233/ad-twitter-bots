from __future__ import annotations

from functools import cached_property
from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import get_settings
from app.core.exceptions import TranscriptionError
from app.services.asr.models import Segment, TranscriptionResult, WordTimestamp


class WhisperASRProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    @cached_property
    def model(self) -> WhisperModel:
        return WhisperModel(
            self.settings.whisper_model,
            device=self.settings.whisper_device,
            compute_type=self.settings.whisper_compute_type,
        )

    def transcribe(self, media_path: Path) -> TranscriptionResult:
        try:
            segments, info = self.model.transcribe(str(media_path), beam_size=self.settings.whisper_beam_size, word_timestamps=True)
            normalized = [
                Segment(
                    text=item.text.strip(),
                    start=float(item.start),
                    end=float(item.end),
                    words=[
                        WordTimestamp(text=word.word.strip(), start=float(word.start), end=float(word.end))
                        for word in (item.words or [])
                    ] or None,
                )
                for item in segments
            ]
            return TranscriptionResult(
                language=info.language,
                duration=info.duration,
                segments=normalized,
                raw_response={"language_probability": info.language_probability},
            )
        except Exception as exc:
            raise TranscriptionError(f"Whisper transcription failed: {exc}") from exc
