from pathlib import Path

from app.core.config import Settings
from app.services.asr.models import Segment, TranscriptionResult
from app.services.subtitles.ass_writer import write_ass


def test_write_ass_includes_cjk_font_and_dialogue(tmp_path: Path) -> None:
    settings = Settings(subtitle_font_name="Noto Sans CJK SC", subtitle_font_size=18)
    result = TranscriptionResult(
        segments=[Segment(text="?? ??", start=0.0, end=2.0)]
    )
    output = tmp_path / "captions.ass"

    write_ass(result, output, settings)

    content = output.read_text(encoding="utf-8-sig")
    assert "Style: Default,Noto Sans CJK SC,18" in content
    assert "Dialogue: 0,0:00:00.00,0:00:02.00" in content
    assert "?? ??" in content
