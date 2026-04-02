from __future__ import annotations

import subprocess
from pathlib import Path


class AudioExtractor:
    def extract(self, video_path: Path, audio_path: Path) -> Path:
        command = ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le", str(audio_path)]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())
        return audio_path
