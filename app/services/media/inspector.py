from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.services.asr.models import VideoMetadata


class FFprobeInspector:
    def inspect(self, file_path: Path) -> VideoMetadata:
        command = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(file_path)]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {proc.stderr.strip()}")
        payload = json.loads(proc.stdout)
        streams = payload.get("streams", [])
        fmt = payload.get("format", {})
        video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
        audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), {})
        fps = None
        frame_rate = video_stream.get("avg_frame_rate")
        if frame_rate and frame_rate != "0/0":
            num, den = frame_rate.split("/")
            fps = float(num) / float(den)
        return VideoMetadata(
            duration_seconds=float(fmt.get("duration", 0.0)),
            filesize_bytes=int(fmt.get("size", file_path.stat().st_size)),
            width=video_stream.get("width"),
            height=video_stream.get("height"),
            fps=fps,
            has_audio=bool(audio_stream),
            audio_codec=audio_stream.get("codec_name"),
            video_codec=video_stream.get("codec_name"),
        )
