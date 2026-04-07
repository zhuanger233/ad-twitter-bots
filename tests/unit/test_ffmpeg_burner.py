from pathlib import Path
from types import SimpleNamespace

from app.services.media.ffmpeg_burner import FFmpegBurner


def test_ffmpeg_burner_uses_utf8_and_cjk_font(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def fake_get_settings():
        return SimpleNamespace(subtitle_font_name="Noto Sans CJK SC", subtitle_font_size=18)

    def fake_run(command, capture_output, text, check):
        commands.append(command)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("app.services.media.ffmpeg_burner.get_settings", fake_get_settings)
    monkeypatch.setattr("app.services.media.ffmpeg_burner.subprocess.run", fake_run)

    FFmpegBurner().burn(tmp_path / "source.mp4", tmp_path / "captions.srt", tmp_path / "output.mp4")

    vf = commands[0][commands[0].index("-vf") + 1]
    assert "charenc=UTF-8" in vf
    assert "FontName=Noto Sans CJK SC" in vf
