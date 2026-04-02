from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.exceptions import FFmpegError


class FFmpegBurner:
    def burn(self, video_path: Path, srt_path: Path, output_path: Path) -> Path:
        subtitle_filter = f"subtitles={srt_path.as_posix()}"
        command = [
            "ffmpeg", "-y", "-i", str(video_path), "-vf", subtitle_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-movflags", "+faststart", str(output_path),
        ]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise FFmpegError(f"ffmpeg burn failed: {proc.stderr.strip()}")
        return output_path
