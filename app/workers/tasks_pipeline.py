from __future__ import annotations

from pathlib import Path
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.clients.r2_client import R2Client
from app.clients.x_client import XClient
from app.core.config import get_settings
from app.core.constants import ASREngine, TaskStage, TaskStatus
from app.core.exceptions import AppError
from app.db.models.subtitle_task import SubtitleTask
from app.db.repositories.subtitle_task_repo import SubtitleTaskRepository
from app.db.session import SessionLocal
from app.services.asr.elevenlabs_provider import ElevenLabsASRProvider
from app.services.asr.whisper_provider import WhisperASRProvider
from app.services.media.downloader import VideoDownloader
from app.services.media.ffmpeg_burner import FFmpegBurner
from app.services.media.inspector import FFprobeInspector
from app.services.media.tempfiles import TaskWorkspace
from app.services.pipeline.router import ASRRouter
from app.services.reply.tweet_replier import TweetReplier
from app.services.subtitles.srt_writer import write_srt
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


def _load_task(session: Session, task_id: str) -> tuple[SubtitleTaskRepository, SubtitleTask]:
    repo = SubtitleTaskRepository(session)
    task = repo.get(UUID(task_id))
    if task is None:
        raise ValueError(f"Task {task_id} not found")
    return repo, task


@celery_app.task(name="app.workers.tasks_pipeline.run_pipeline", bind=True, max_retries=3)
def run_pipeline(self, task_id: str) -> str:
    settings = get_settings()
    with SessionLocal() as session:
        repo, task = _load_task(session, task_id)
        try:
            logger.info("pipeline started task_id=%s mention_tweet_id=%s video_tweet_id=%s", task.id, task.mention_tweet_id, task.video_tweet_id or "-")
            repo.update_stage(task, stage=TaskStage.DETECTED, status=TaskStatus.PROCESSING)
            x_client = XClient()
            resolved = x_client.resolve_video_source(task.mention_tweet_id, task.video_tweet_id)
            logger.info("pipeline resolved video task_id=%s resolved_video_tweet_id=%s video_url=%s", task.id, resolved.get("resolved_video_tweet_id", "-"), resolved.get("video_url", "-"))
            task.video_tweet_id = str(resolved.get("resolved_video_tweet_id", task.video_tweet_id or task.mention_tweet_id))
            task.video_url = resolved["video_url"]
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.RESOLVED_VIDEO)

            workspace = TaskWorkspace(settings, task.id)
            source_path = workspace.child("source.mp4")
            VideoDownloader().download(task.video_url, source_path)
            task.source_video_path = str(source_path)
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.DOWNLOADED)

            metadata = FFprobeInspector().inspect(source_path)
            logger.info("pipeline inspected media task_id=%s duration_seconds=%s filesize_bytes=%s", task.id, metadata.duration_seconds, metadata.filesize_bytes)
            task.duration_seconds = metadata.duration_seconds
            task.filesize_bytes = metadata.filesize_bytes
            task.asr_engine = ASRRouter(settings).choose_engine(metadata).value
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.INSPECTED)
            repo.update_stage(task, stage=TaskStage.TRANSCRIBING)

            if task.asr_engine == ASREngine.ELEVENLABS.value:
                transcription_result = ElevenLabsASRProvider().transcribe(source_path)
            else:
                transcription_result = WhisperASRProvider().transcribe(source_path)
            logger.info("pipeline transcription completed task_id=%s asr_engine=%s segments=%s", task.id, task.asr_engine, len(transcription_result.segments))

            srt_path = workspace.child("captions.srt")
            write_srt(transcription_result, srt_path, settings)
            logger.info("pipeline wrote subtitles task_id=%s srt_path=%s", task.id, srt_path)
            repo.update_stage(task, stage=TaskStage.SUBTITLE_GENERATED)

            burned_path = workspace.child("output.mp4")
            FFmpegBurner().burn(source_path, srt_path, burned_path)
            logger.info("pipeline burned video task_id=%s output_path=%s", task.id, burned_path)
            task.output_video_path = str(burned_path)
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.BURNED)

            task.backup_url = R2Client().upload(burned_path)
            logger.info("pipeline uploaded backup task_id=%s backup_url=%s", task.id, task.backup_url)
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.UPLOADED_BACKUP)

            media_id, reply_tweet_id = TweetReplier().upload_and_reply(
                mention_tweet_id=task.mention_tweet_id,
                output_video_path=Path(burned_path),
                text="Subtitle generated. Attached processed video.",
            )
            task.x_media_id = media_id
            task.reply_tweet_id = reply_tweet_id
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.UPLOADED_X)
            repo.update_stage(task, stage=TaskStage.REPLIED)
            repo.mark_completed(task)
            logger.info("pipeline completed task_id=%s reply_tweet_id=%s media_id=%s", task.id, reply_tweet_id, media_id)
            return str(task.id)
        except AppError as exc:
            logger.exception("pipeline failed with app error task_id=%s code=%s message=%s", task.id, exc.code.value, exc.message)
            repo.mark_failed(task, error_code=exc.code.value, error_message=exc.message)
            raise
        except Exception as exc:
            logger.exception("pipeline failed with unexpected error task_id=%s", task.id)
            repo.mark_failed(task, error_code="INTERNAL_ERROR", error_message=str(exc))
            raise


@celery_app.task(name="app.workers.tasks_pipeline.resolve_video")
def resolve_video(task_id: str) -> str:
    return task_id


@celery_app.task(name="app.workers.tasks_pipeline.download_video")
def download_video(task_id: str) -> str:
    return task_id


@celery_app.task(name="app.workers.tasks_pipeline.inspect_video")
def inspect_video(task_id: str) -> str:
    return task_id
