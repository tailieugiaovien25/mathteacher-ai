"""Self-contained, teacher-controlled audio assets for the offline classroom stage.

The short effects originate from the user's lucky-wheel presentation. The
wheel track is stored for a later wheel UI; ordinary questions do not load it.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path


_TRACKS = {
    "question": ("media1.mp3", "audio/mpeg"),
    "final": ("media2.mp3", "audio/mpeg"),
    "win": ("media3.mp3", "audio/mpeg"),
    "lose": ("media4.mp3", "audio/mpeg"),
    "select": ("select.wav", "audio/wav"),
    "reveal": ("reveal.wav", "audio/wav"),
    "wheel": ("wheel.wav", "audio/wav"),
}


@lru_cache(maxsize=2)
def stage_audio_sources(*, include_wheel: bool = False) -> dict[str, str]:
    """Data URLs remain inside the downloaded HTML for use without internet."""
    folder = Path(__file__).with_name("classroom_audio")
    result = {}
    for role, (filename, mime) in _TRACKS.items():
        if role == "wheel" and not include_wheel:
            continue
        path = folder / filename
        if not path.is_file():
            raise FileNotFoundError(f"Thiếu âm thanh sân khấu: {path}")
        result[role] = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    return result
