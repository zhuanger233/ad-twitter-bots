from __future__ import annotations

from pathlib import Path

import httpx

from app.core.constants import ErrorCode
from app.core.exceptions import AppError


class VideoDownloader:
    def __init__(self, timeout_seconds: float = 120.0) -> None:
        self.timeout_seconds = timeout_seconds

    def download(self, url: str, output_path: Path) -> Path:
        try:
            with httpx.stream("GET", url, timeout=self.timeout_seconds, follow_redirects=True) as response:
                response.raise_for_status()
                with output_path.open("wb") as file_obj:
                    for chunk in response.iter_bytes():
                        file_obj.write(chunk)
        except Exception as exc:
            raise AppError(
                f"Failed to download video from {url}: {exc}",
                code=ErrorCode.VIDEO_DOWNLOAD_FAILED,
                retryable=True,
            ) from exc
        return output_path
