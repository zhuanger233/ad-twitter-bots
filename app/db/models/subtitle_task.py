from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ASREngine, TaskStage, TaskStatus
from app.db.base import Base


class SubtitleTask(Base):
    __tablename__ = "subtitle_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    mention_tweet_id: Mapped[str] = mapped_column(String(64), index=True)
    video_tweet_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    request_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.QUEUED.value, index=True)
    stage: Mapped[str] = mapped_column(String(32), default=TaskStage.DETECTED.value)
    asr_engine: Mapped[str | None] = mapped_column(String(32), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    dedupe_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_video_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_video_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    backup_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    x_media_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reply_tweet_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    filesize_bytes: Mapped[int | None] = mapped_column(nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def typed_status(self) -> TaskStatus:
        return TaskStatus(self.status)

    @property
    def typed_stage(self) -> TaskStage:
        return TaskStage(self.stage)

    @property
    def typed_asr_engine(self) -> ASREngine | None:
        return ASREngine(self.asr_engine) if self.asr_engine else None
