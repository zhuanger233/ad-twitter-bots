from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.services.asr.models import TranscriptionResult
from app.services.subtitles.formatter import build_blocks
from app.services.subtitles.segmentation import segment_for_srt


def format_srt_timestamp(value: float) -> str:
    hours = int(value // 3600)
    minutes = int((value % 3600) // 60)
    seconds = int(value % 60)
    milliseconds = int(round((value - int(value)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def write_srt(result: TranscriptionResult, output_path: Path, settings: Settings) -> Path:
    segments = segment_for_srt(result.segments, settings)
    blocks = build_blocks(segments, settings)
    lines: list[str] = []
    for block in blocks:
        lines.extend([
            str(block.index),
            f"{format_srt_timestamp(block.start)} --> {format_srt_timestamp(block.end)}",
            *block.lines,
            "",
        ])
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
