from __future__ import annotations

from app.core.config import Settings
from app.services.asr.models import Segment, WordTimestamp


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
        if _should_split_by_words(segment, settings):
            normalized.extend(_split_segment_by_words(segment, settings))
            continue
        duration = max(segment.end - segment.start, settings.min_block_duration)
        capped_end = min(segment.start + duration, segment.start + settings.max_block_duration)
        normalized.append(Segment(text=text, start=segment.start, end=max(capped_end, segment.end), words=segment.words))
    return normalized


def _should_split_by_words(segment: Segment, settings: Settings) -> bool:
    if not segment.words:
        return False
    text = " ".join(segment.text.split())
    max_chars_total = settings.max_chars_per_line * settings.max_lines_per_block
    duration = segment.end - segment.start
    return duration > settings.max_block_duration or len(text) > max_chars_total


def _split_segment_by_words(segment: Segment, settings: Settings) -> list[Segment]:
    words = [word for word in (segment.words or []) if word.text.strip()]
    if not words:
        return [Segment(text=" ".join(segment.text.split()), start=segment.start, end=segment.end, words=segment.words)]

    max_chars_total = settings.max_chars_per_line * settings.max_lines_per_block
    chunks: list[list[WordTimestamp]] = []
    current: list[WordTimestamp] = []

    for word in words:
        candidate = current + [word]
        if current and _should_break_chunk(current, candidate, settings, max_chars_total):
            chunks.append(current)
            current = [word]
        else:
            current = candidate
            if _should_close_on_punctuation(current, settings):
                chunks.append(current)
                current = []
    if current:
        chunks.append(current)

    return [_segment_from_word_chunk(chunk, settings) for chunk in chunks if chunk]


def _should_break_chunk(current: list[WordTimestamp], candidate: list[WordTimestamp], settings: Settings, max_chars_total: int) -> bool:
    candidate_text = _join_words(candidate)
    candidate_duration = candidate[-1].end - candidate[0].start
    gap = candidate[-1].start - current[-1].end
    return (
        len(candidate_text) > max_chars_total
        or candidate_duration > settings.max_block_duration
        or gap >= 1.0
    )


def _should_close_on_punctuation(words: list[WordTimestamp], settings: Settings) -> bool:
    if not words:
        return False
    duration = words[-1].end - words[0].start
    if duration < settings.min_block_duration:
        return False
    return words[-1].text.strip().endswith((".", ",", "!", "?", ";", ":"))


def _segment_from_word_chunk(words: list[WordTimestamp], settings: Settings) -> Segment:
    text = _join_words(words)
    start = float(words[0].start)
    raw_end = float(words[-1].end)
    end = max(raw_end, start + settings.min_block_duration)
    end = min(end, start + settings.max_block_duration)
    return Segment(text=text, start=start, end=max(end, raw_end), words=words)


def _join_words(words: list[WordTimestamp]) -> str:
    return " ".join(word.text.strip() for word in words if word.text.strip())
