from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.services.asr.models import Segment
from app.services.subtitles.segmentation import split_text


@dataclass(slots=True)
class SubtitleBlock:
    index: int
    start: float
    end: float
    lines: list[str]


def build_blocks(segments: list[Segment], settings: Settings) -> list[SubtitleBlock]:
    blocks: list[SubtitleBlock] = []
    for index, segment in enumerate(segments, start=1):
        lines = split_text(segment.text, settings.max_chars_per_line)
        lines = lines[: settings.max_lines_per_block]
        blocks.append(SubtitleBlock(index=index, start=segment.start, end=segment.end, lines=lines))
    return blocks
