from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.services.asr.models import TranscriptionResult


class ASRProvider(Protocol):
    def transcribe(self, media_path: Path) -> TranscriptionResult:
        ...
