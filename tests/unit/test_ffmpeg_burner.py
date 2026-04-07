from pathlib import Path
from types import SimpleNamespace

from app.services.media.ffmpeg_burner import FFmpegBurner


def test_ffmpeg_burner_uses_ass_filter_for_ass_subtitles(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def fake_run(command, capture_output, text, check):
        commands.append(command)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("app.services.media.ffmpeg_burner.subprocess.run", fake_run)

    FFmpegBurner().burn(tmp_path / "source.mp4", tmp_path / "captions.ass", tmp_path / "output.mp4")

    vf = commands[0][commands[0].index("-vf") + 1]
    assert vf.endswith("captions.ass")
    assert vf.startswith("ass=")
    assert "force_style" not in vf


def test_ffmpeg_burner_uses_utf8_for_srt_subtitles(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def fake_run(command, capture_output, text, check):
        commands.append(command)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("app.services.media.ffmpeg_burner.subprocess.run", fake_run)

    FFmpegBurner().burn(tmp_path / "source.mp4", tmp_path / "captions.srt", tmp_path / "output.mp4")

    vf = commands[0][commands[0].index("-vf") + 1]
    assert "subtitles=" in vf
    assert "charenc=UTF-8" in vf
