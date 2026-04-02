from __future__ import annotations

from app.core.config import Settings
from app.services.asr.models import Segment


def split_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= max_chars:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def segment_for_srt(segments: list[Segment], settings: Settings) -> list[Segment]:
    normalized: list[Segment] = []
    for segment in segments:
        text = " ".join(segment.text.split())
        if not text:
            continue
        duration = max(segment.end - segment.start, settings.min_block_duration)
        capped_end = min(segment.start + duration, segment.start + settings.max_block_duration)
        normalized.append(Segment(text=text, start=segment.start, end=max(capped_end, segment.end)))
    return normalized
