from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.services.asr.models import TranscriptionResult
from app.services.subtitles.formatter import build_blocks
from app.services.subtitles.segmentation import segment_for_srt


def format_ass_timestamp(value: float) -> str:
    centiseconds = int(round(value * 100))
    hours = centiseconds // 360000
    centiseconds %= 360000
    minutes = centiseconds // 6000
    centiseconds %= 6000
    seconds = centiseconds // 100
    centiseconds %= 100
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def write_ass(result: TranscriptionResult, output_path: Path, settings: Settings) -> Path:
    segments = segment_for_srt(result.segments, settings)
    blocks = build_blocks(segments, settings)
    font_name = _escape_ass_text(settings.subtitle_font_name)
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.709",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font_name},{settings.subtitle_font_size},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,2,40,40,28,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    newline = chr(92) + "N"
    for block in blocks:
        text = newline.join(_escape_ass_text(line) for line in block.lines)
        lines.append(
            f"Dialogue: 0,{format_ass_timestamp(block.start)},{format_ass_timestamp(block.end)},Default,,0,0,0,,{text}"
        )
    output_path.write_text(chr(10).join(lines) + chr(10), encoding="utf-8-sig")
    return output_path


def _escape_ass_text(value: str) -> str:
    backslash = chr(92)
    return value.replace(backslash, backslash + backslash).replace("{", backslash + "{").replace("}", backslash + "}")
