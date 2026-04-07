from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import FFmpegError


class FFmpegBurner:
    def burn(self, video_path: Path, srt_path: Path, output_path: Path) -> Path:
        settings = get_settings()
        subtitle_path = srt_path.as_posix()
        force_style = (
            f"FontName={settings.subtitle_font_name},"
            f"FontSize={settings.subtitle_font_size},"
            "Outline=1,Shadow=0,MarginV=28"
        )
        subtitle_filter = f"subtitles={subtitle_path}:charenc=UTF-8:force_style={force_style}"
        command = [
            "ffmpeg", "-y", "-i", str(video_path), "-vf", subtitle_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-movflags", "+faststart", str(output_path),
        ]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise FFmpegError(f"ffmpeg burn failed: {proc.stderr.strip()}")
        return output_path
