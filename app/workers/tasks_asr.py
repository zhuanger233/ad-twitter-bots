from __future__ import annotations

from pathlib import Path

from app.core.constants import ASREngine
from app.services.asr.elevenlabs_provider import ElevenLabsASRProvider
from app.services.asr.models import TranscriptionResult
from app.services.asr.whisper_provider import WhisperASRProvider
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks_asr.transcribe_media")
def transcribe_media(asr_engine: str, media_path: str) -> dict:
    provider = ElevenLabsASRProvider() if asr_engine == ASREngine.ELEVENLABS.value else WhisperASRProvider()
    result: TranscriptionResult = provider.transcribe(Path(media_path))
    return result.model_dump()
