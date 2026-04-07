from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.exceptions import FFmpegError


class FFmpegBurner:
    def burn(self, video_path: Path, subtitle_path: Path, output_path: Path) -> Path:
        subtitle_filter = f"ass={subtitle_path.as_posix()}" if subtitle_path.suffix.lower() == ".ass" else f"subtitles={subtitle_path.as_posix()}:charenc=UTF-8"
        command = [
            "ffmpeg", "-y", "-i", str(video_path), "-vf", subtitle_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-movflags", "+faststart", str(output_path),
        ]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise FFmpegError(f"ffmpeg burn failed: {proc.stderr.strip()}")
        return output_path
