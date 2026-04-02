from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.clients.r2_client import R2Client
from app.clients.x_client import XClient
from app.core.config import get_settings
from app.core.constants import TaskStage, TaskStatus
from app.core.exceptions import AppError
from app.db.models.subtitle_task import SubtitleTask
from app.db.repositories.subtitle_task_repo import SubtitleTaskRepository
from app.db.session import SessionLocal
from app.services.media.downloader import VideoDownloader
from app.services.media.inspector import FFprobeInspector
from app.services.media.tempfiles import TaskWorkspace
from app.services.pipeline.router import ASRRouter
from app.workers.celery_app import celery_app
from app.workers.tasks_asr import transcribe_media
from app.workers.tasks_ffmpeg import burn_subtitles, generate_srt
from app.workers.tasks_post import upload_and_reply


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
            repo.update_stage(task, stage=TaskStage.DETECTED, status=TaskStatus.PROCESSING)
            x_client = XClient()
            resolved = x_client.resolve_video_source(task.mention_tweet_id, task.video_tweet_id)
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
            task.duration_seconds = metadata.duration_seconds
            task.filesize_bytes = metadata.filesize_bytes
            task.asr_engine = ASRRouter(settings).choose_engine(metadata).value
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.INSPECTED)
            repo.update_stage(task, stage=TaskStage.TRANSCRIBING)

            transcription_payload = transcribe_media.delay(task.asr_engine, str(source_path)).get(timeout=3600)
            srt_path = workspace.child("captions.srt")
            generate_srt.delay(transcription_payload, str(srt_path)).get(timeout=120)
            repo.update_stage(task, stage=TaskStage.SUBTITLE_GENERATED)

            burned_path = workspace.child("output.mp4")
            burn_subtitles.delay(str(source_path), str(srt_path), str(burned_path)).get(timeout=1800)
            task.output_video_path = str(burned_path)
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.BURNED)

            task.backup_url = R2Client().upload(burned_path)
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.UPLOADED_BACKUP)

            post_result = upload_and_reply.delay(task.mention_tweet_id, str(burned_path), "Subtitle generated. Attached processed video.").get(timeout=600)
            task.x_media_id = post_result["media_id"]
            task.reply_tweet_id = post_result["reply_tweet_id"]
            session.add(task)
            session.commit()
            session.refresh(task)
            repo.update_stage(task, stage=TaskStage.UPLOADED_X)
            repo.update_stage(task, stage=TaskStage.REPLIED)
            repo.mark_completed(task)
            return str(task.id)
        except AppError as exc:
            repo.mark_failed(task, error_code=exc.code.value, error_message=exc.message)
            raise
        except Exception as exc:
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
