from __future__ import annotations

import shutil
from pathlib import Path
from uuid import UUID

from app.core.config import Settings


class TaskWorkspace:
    def __init__(self, settings: Settings, task_id: UUID) -> None:
        self.path = settings.workdir / settings.temp_dir_name / str(task_id)
        self.path.mkdir(parents=True, exist_ok=True)

    def child(self, name: str) -> Path:
        return self.path / name

    def cleanup(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path, ignore_errors=True)
