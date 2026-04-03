from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    workdir: Path = Field(default=Path("./workdir"))

    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/subtitle_bot"

    x_api_key: str = ""
    x_api_secret: str = ""
    x_access_token: str = ""
    x_access_token_secret: str = ""
    x_bearer_token: str = ""
    x_bot_username: str = ""
    x_bot_user_id: str = ""
    x_webhook_validation_enabled: bool = True

    elevenlabs_api_key: str = ""
    elevenlabs_model_id: str = "scribe_v2"
    elevenlabs_timeout_seconds: float = 120.0

    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_beam_size: int = 5

    elevenlabs_max_duration_seconds: float = 300.0
    elevenlabs_max_filesize_mb: int = 25
    hard_max_video_duration_seconds: float = 3600.0
    hard_max_filesize_mb: int = 512

    mention_poll_interval_seconds: int = 60
    mention_lookback_limit: int = 20

    max_chars_per_line: int = 42
    max_lines_per_block: int = 2
    min_block_duration: float = 1.2
    max_block_duration: float = 6.0

    admin_token: str = "local-admin-token"
    public_base_url: str = "http://localhost:8000"
    temp_dir_name: str = "tasks"
    x_api_base_url: str = "https://api.x.com"
    elevenlabs_api_base_url: str = "https://api.elevenlabs.io"

    def ensure_workdirs(self) -> None:
        self.workdir.mkdir(parents=True, exist_ok=True)
        (self.workdir / self.temp_dir_name).mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_workdirs()
    return settings
