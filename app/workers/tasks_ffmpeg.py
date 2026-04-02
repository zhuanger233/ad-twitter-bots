from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.services.asr.models import TranscriptionResult
from app.services.media.ffmpeg_burner import FFmpegBurner
from app.services.subtitles.srt_writer import write_srt
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks_ffmpeg.generate_srt")
def generate_srt(transcription_payload: dict, output_path: str) -> str:
    result = TranscriptionResult.model_validate(transcription_payload)
    settings = get_settings()
    return str(write_srt(result, Path(output_path), settings))


@celery_app.task(name="app.workers.tasks_ffmpeg.burn_subtitles")
def burn_subtitles(video_path: str, srt_path: str, output_path: str) -> str:
    burner = FFmpegBurner()
    return str(burner.burn(Path(video_path), Path(srt_path), Path(output_path)))
