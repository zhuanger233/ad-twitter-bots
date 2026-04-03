from pathlib import Path

from app.core.config import Settings
from app.services.asr.models import Segment, TranscriptionResult, WordTimestamp
from app.services.subtitles.segmentation import segment_for_srt
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


def test_segment_for_srt_splits_long_word_timestamps_into_multiple_blocks() -> None:
    settings = Settings(max_chars_per_line=12, max_lines_per_block=2, max_block_duration=3.0)
    long_segment = Segment(
        text="one two three four five six seven eight nine ten eleven twelve",
        start=0.0,
        end=6.1,
        words=[
            WordTimestamp(text="one", start=0.0, end=0.3),
            WordTimestamp(text="two", start=0.35, end=0.6),
            WordTimestamp(text="three", start=0.65, end=1.0),
            WordTimestamp(text="four", start=1.05, end=1.3),
            WordTimestamp(text="five", start=1.35, end=1.6),
            WordTimestamp(text="six", start=1.65, end=1.9),
            WordTimestamp(text="seven", start=2.2, end=2.5),
            WordTimestamp(text="eight", start=2.55, end=2.85),
            WordTimestamp(text="nine", start=3.2, end=3.45),
            WordTimestamp(text="ten", start=3.5, end=3.75),
            WordTimestamp(text="eleven", start=4.0, end=4.4),
            WordTimestamp(text="twelve", start=5.5, end=6.1),
        ],
    )

    segments = segment_for_srt([long_segment], settings)

    assert len(segments) >= 2
    assert segments[0].start == 0.0
    assert segments[-1].end >= 6.1
    assert all(segment.end > segment.start for segment in segments)
    assert all(len(segment.text) <= settings.max_chars_per_line * settings.max_lines_per_block for segment in segments)
