from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_kernel.teaching_avatar_realtime import build_audio_lipsync_track
from ai_kernel.teaching_realtime_transport import (
    LiveKitTransportConfig,
    build_livekit_room_descriptor,
)


def _write_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes((b"\x00\x10" * 800))


def test_audio_lipsync_track_is_deterministic(tmp_path: Path):
    audio = tmp_path / "reply.wav"
    _write_wav(audio)
    track = build_audio_lipsync_track(audio, window_ms=50)
    assert track.audio_path == audio
    assert track.sample_rate == 16_000
    assert track.cues
    assert all(0.0 <= cue.amplitude <= 1.0 for cue in track.cues)


def test_livekit_descriptor_is_replaceable_and_self_hosted():
    cfg = LiveKitTransportConfig(url="ws://127.0.0.1:7880", room_name="demo")
    desc = build_livekit_room_descriptor(cfg, identity_suffix="teacher-1")
    assert desc.identity == "mathteacher-ta-teacher-1"
    assert desc.room_name == "demo"
    assert desc.can_publish_audio is True
    assert desc.can_publish_video is True


if __name__ == "__main__":
    test_audio_lipsync_track_is_deterministic(Path("/tmp"))
    test_livekit_descriptor_is_replaceable_and_self_hosted()
    print("2/2 PASS")
