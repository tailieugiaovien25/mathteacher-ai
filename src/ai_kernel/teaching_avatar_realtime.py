from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import wave


@dataclass(frozen=True)
class MouthCue:
    time_s: float
    amplitude: float


@dataclass(frozen=True)
class AudioLipSyncTrack:
    audio_path: Path
    sample_rate: int
    cues: tuple[MouthCue, ...]


def build_audio_lipsync_track(
    audio_path: str | Path,
    *,
    window_ms: int = 50,
) -> AudioLipSyncTrack:
    """Build a lightweight mouth-cue track from a PCM WAV file.

    It is intentionally dependency-free. The browser can also run its own
    WebAudio analyser; this track is a deterministic fallback for tests and
    non-WebAudio renderers.
    """

    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(path)
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        if sample_width != 2:
            raise ValueError("Lip-sync track hiện yêu cầu WAV PCM 16-bit.")
        frames = wav.readframes(wav.getnframes())

    frame_size = channels * sample_width
    frames_per_window = max(1, int(sample_rate * window_ms / 1000))
    cues: list[MouthCue] = []
    for start in range(0, len(frames), frames_per_window * frame_size):
        window = frames[start:start + frames_per_window * frame_size]
        if not window:
            continue
        samples = []
        for index in range(0, len(window), 2):
            value = int.from_bytes(window[index:index + 2], "little", signed=True) / 32768.0
            samples.append(value)
        rms = math.sqrt(sum(v * v for v in samples) / max(1, len(samples)))
        amplitude = max(0.0, min(1.0, rms * 3.5))
        cues.append(
            MouthCue(
                time_s=(start / frame_size) / max(1, sample_rate),
                amplitude=amplitude,
            )
        )
    return AudioLipSyncTrack(path, sample_rate, tuple(cues))


__all__ = ["AudioLipSyncTrack", "MouthCue", "build_audio_lipsync_track"]
