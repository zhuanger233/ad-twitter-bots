from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260402_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subtitle_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("mention_tweet_id", sa.String(length=64), nullable=False),
        sa.Column("video_tweet_id", sa.String(length=64), nullable=True),
        sa.Column("request_user_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("asr_engine", sa.String(length=32), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=128), nullable=False),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("source_video_path", sa.Text(), nullable=True),
        sa.Column("output_video_path", sa.Text(), nullable=True),
        sa.Column("backup_url", sa.Text(), nullable=True),
        sa.Column("x_media_id", sa.String(length=128), nullable=True),
        sa.Column("reply_tweet_id", sa.String(length=64), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("filesize_bytes", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("ix_subtitle_tasks_mention_tweet_id", "subtitle_tasks", ["mention_tweet_id"])
    op.create_index("ix_subtitle_tasks_video_tweet_id", "subtitle_tasks", ["video_tweet_id"])
    op.create_index("ix_subtitle_tasks_status", "subtitle_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_subtitle_tasks_status", table_name="subtitle_tasks")
    op.drop_index("ix_subtitle_tasks_video_tweet_id", table_name="subtitle_tasks")
    op.drop_index("ix_subtitle_tasks_mention_tweet_id", table_name="subtitle_tasks")
    op.drop_table("subtitle_tasks")
