from pathlib import Path
import sys
import tempfile
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import importlib.util
import sys

_MODULE_PATH = Path(__file__).resolve().parents[1] / "ai_kernel" / "teaching_avatar.py"
_spec = importlib.util.spec_from_file_location("teaching_avatar_v13d", _MODULE_PATH)
_teaching_avatar = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules[_spec.name] = _teaching_avatar
_spec.loader.exec_module(_teaching_avatar)

AvatarState = _teaching_avatar.AvatarState
AvatarProfile = _teaching_avatar.AvatarProfile
CommandLipSyncProvider = _teaching_avatar.CommandLipSyncProvider
StaticAvatarRenderer = _teaching_avatar.StaticAvatarRenderer
TeachingAvatarSession = _teaching_avatar.TeachingAvatarSession


def make_wav(path: Path) -> Path:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16_000)
        wf.writeframes(b"\x00\x00" * 160)
    return path


def test_static_avatar_state_and_speak_without_lipsync():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        avatar = root / "avatar.png"
        avatar.write_bytes(b"fake-png")
        audio = make_wav(root / "reply.wav")
        session = TeachingAvatarSession(
            profile=AvatarProfile("a1", "Trợ giảng", avatar),
            renderer=StaticAvatarRenderer(),
        )
        idle = session.set_state(AvatarState.IDLE)
        speak = session.speak(audio_path=audio)
        assert idle.state is AvatarState.IDLE
        assert speak.state is AvatarState.SPEAKING
        assert speak.media_path == avatar
        assert speak.audio_path == audio


def test_command_lipsync_placeholder_contract():
    provider = CommandLipSyncProvider(["python", "-c", "from pathlib import Path; Path('{output}').write_bytes(Path('{audio}').read_bytes())", "{avatar}", "{audio}", "{output}"], provider_id="fake-lipsync")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        avatar = root / "avatar.png"
        audio = make_wav(root / "audio.wav")
        output = root / "result.mp4"
        avatar.write_bytes(b"fake")
        result = provider.synthesize(avatar_image=avatar, audio_path=audio, output_path=output)
        assert result == output
        assert output.exists()
        assert output.read_bytes() == audio.read_bytes()


def test_missing_avatar_is_rejected_before_render():
    missing = Path(tempfile.gettempdir()) / "mathteacher_missing_avatar_v13d.png"
    session = TeachingAvatarSession(
        profile=AvatarProfile("a1", "Trợ giảng", missing),
        renderer=StaticAvatarRenderer(),
    )
    try:
        session.set_state(AvatarState.IDLE)
    except FileNotFoundError:
        return
    raise AssertionError("Expected missing avatar to be rejected")


if __name__ == "__main__":
    test_static_avatar_state_and_speak_without_lipsync()
    test_command_lipsync_placeholder_contract()
    test_missing_avatar_is_rejected_before_render()
    print("3/3 PASS")
