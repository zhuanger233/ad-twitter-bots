from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings


class ElevenLabsClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @retry(
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(httpx.TransportError),
        reraise=True,
    )
    def transcribe(self, media_path: Path) -> dict[str, Any]:
        with media_path.open("rb") as file_obj:
            response = httpx.post(
                f"{self.settings.elevenlabs_api_base_url}/v1/speech-to-text",
                headers={"xi-api-key": self.settings.elevenlabs_api_key},
                files={"file": (media_path.name, file_obj, "video/mp4")},
                data={
                    "model_id": self.settings.elevenlabs_model_id,
                    "timestamps_granularity": "word",
                },
                timeout=self.settings.elevenlabs_timeout_seconds,
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            raise httpx.HTTPStatusError(
                f"{exc}. Response body: {detail}",
                request=exc.request,
                response=exc.response,
            ) from exc
        return response.json()
