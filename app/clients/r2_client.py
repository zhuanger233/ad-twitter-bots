from __future__ import annotations

from pathlib import Path


class R2Client:
    def upload(self, file_path: Path) -> str:
        return f"mock://backup/{file_path.name}"
