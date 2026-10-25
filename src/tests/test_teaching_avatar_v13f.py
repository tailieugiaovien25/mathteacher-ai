from pathlib import Path
import importlib.util
import tempfile
import wave
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_kernel.teaching_avatar_realtime import build_audio_lipsync_track
from ai_kernel.teaching_realtime_transport import (
    LiveKitTransportConfig,
    build_livekit_room_descriptor,
    livekit_environment_status,
)


def _load_surface_module():
    path = ROOT / "portal_v2" / "ui" / "teaching_assistant_avatar_surface_streamlit.py"
    spec = importlib.util.spec_from_file_location("ta_surface_v13f", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes((b"\x00\x10" * 1600))


def test_local_browser_lipsync_track():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "voice.wav"
        _write_wav(path)
        track = build_audio_lipsync_track(path, window_ms=50)
        assert len(track.cues) > 0
        assert track.sample_rate == 16_000
        assert all(0 <= cue.amplitude <= 1 for cue in track.cues)


def test_avatar_surface_embeds_audio_web_audio_lipsync():
    module = _load_surface_module()
    html = module.build_avatar_surface_html(
        avatar_svg='<svg><path id="avatar-mouth" d="M0 0"/></svg>',
        display_name="Trợ giảng Toán",
        state="speaking",
        audio_data_uri="data:audio/wav;base64,AAAA",
    )
    assert "ta-audio" in html
    assert "AudioContext" in html
    assert "avatar-mouth" in html
    assert "data:audio/wav;base64,AAAA" in html
    assert "classroom.slide.open" not in html


def test_livekit_transport_descriptor_is_replaceable():
    config = LiveKitTransportConfig(url="ws://127.0.0.1:7880", room_name="demo")
    descriptor = build_livekit_room_descriptor(config, identity_suffix="teacher")
    status = livekit_environment_status(config)
    assert descriptor.identity == "mathteacher-ta-teacher"
    assert descriptor.room_name == "demo"
    assert status["self_hosted"] is True
    assert status["transport"] == "livekit"


if __name__ == "__main__":
    test_local_browser_lipsync_track()
    test_avatar_surface_embeds_audio_web_audio_lipsync()
    test_livekit_transport_descriptor_is_replaceable()
    print("3/3 PASS")
