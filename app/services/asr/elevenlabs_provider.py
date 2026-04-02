from __future__ import annotations

from pathlib import Path

from app.clients.elevenlabs_client import ElevenLabsClient
from app.core.exceptions import TranscriptionError
from app.services.asr.models import Segment, TranscriptionResult, WordTimestamp


class ElevenLabsASRProvider:
    def __init__(self, client: ElevenLabsClient | None = None) -> None:
        self.client = client or ElevenLabsClient()

    def transcribe(self, media_path: Path) -> TranscriptionResult:
        try:
            payload = self.client.transcribe(media_path)
            words_payload = payload.get("words", [])
            segments_payload = payload.get("segments") or []
            if segments_payload:
                segments = [
                    Segment(
                        text=item["text"],
                        start=float(item["start"]),
                        end=float(item["end"]),
                        words=[
                            WordTimestamp(text=word["text"], start=float(word["start"]), end=float(word["end"]))
                            for word in item.get("words", [])
                        ] or None,
                    )
                    for item in segments_payload
                ]
            else:
                text = " ".join(word["text"] for word in words_payload).strip()
                start = float(words_payload[0]["start"]) if words_payload else 0.0
                end = float(words_payload[-1]["end"]) if words_payload else 0.0
                segments = [
                    Segment(
                        text=text,
                        start=start,
                        end=end,
                        words=[
                            WordTimestamp(text=word["text"], start=float(word["start"]), end=float(word["end"]))
                            for word in words_payload
                        ] or None,
                    )
                ]
            return TranscriptionResult(
                language=payload.get("language_code"),
                duration=payload.get("duration_seconds"),
                segments=segments,
                raw_response=payload,
            )
        except Exception as exc:
            raise TranscriptionError(f"ElevenLabs transcription failed: {exc}") from exc
