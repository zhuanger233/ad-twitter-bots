from pathlib import Path

from app.core.config import Settings
from app.services.asr.models import Segment, TranscriptionResult
from app.services.subtitles.srt_writer import write_srt


def test_write_srt_creates_expected_blocks(tmp_path: Path) -> None:
    settings = Settings()
    result = TranscriptionResult(
        segments=[
            Segment(text="hello world from subtitle bot", start=0.0, end=2.2),
            Segment(text="this is another line", start=2.3, end=4.5),
        ]
    )
    output = tmp_path / "captions.srt"
    write_srt(result, output, settings)
    content = output.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:02,200" in content
    assert "hello world from subtitle bot" in content
    assert "this is another line" in content
