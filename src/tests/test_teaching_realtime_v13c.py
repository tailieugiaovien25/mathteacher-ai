from pathlib import Path

from ai_kernel.teaching_realtime import EnergyVoiceActivityDetector, RealtimeTeachingSession, RealtimeVoiceConfig
from ai_kernel.teaching_voice import STTResult, TeachingAssistantVoiceBridge


class FakeMic:
    def __init__(self, path: Path):
        self.path = path
        self.calls = 0

    def record_utterance(self, *, config):
        self.calls += 1
        return self.path


class FakeSTT:
    def transcribe(self, audio_path, *, language="vi"):
        return STTResult(text="Xin chào trợ giảng.", provider="fake", language=language)


class FakeBrain:
    def respond(self, *, transcript, system_prompt, history=()):
        return "Xin chào thầy/cô. Em sẵn sàng hỗ trợ."


def test_vad_detects_start_and_end():
    vad = EnergyVoiceActivityDetector(threshold=0.01, silence_timeout_ms=60)
    speech = (1000).to_bytes(2, "little", signed=True) * 480
    silence = b"\x00\x00" * 480
    active, ended = vad.feed(speech, block_ms=30)
    assert active and not ended
    _, ended = vad.feed(silence, block_ms=30)
    assert not ended
    _, ended = vad.feed(silence, block_ms=30)
    assert ended


def test_realtime_session_runs_one_turn(tmp_path):
    audio = tmp_path / "input.wav"
    audio.write_bytes(b"fake")
    bridge = TeachingAssistantVoiceBridge(stt=FakeSTT(), brain=FakeBrain())
    session = RealtimeTeachingSession(
        microphone=FakeMic(audio),
        voice_bridge=bridge,
        config=RealtimeVoiceConfig(),
    )
    events = list(session.run(max_turns=1))
    states = [event.state for event in events]
    assert states == ["session_started", "listening", "processing", "turn_completed", "session_stopped"]
    assert events[3].turn.response_text.startswith("Xin chào")


def test_realtime_session_does_not_execute_classroom_tools(tmp_path):
    audio = tmp_path / "input.wav"
    audio.write_bytes(b"fake")
    bridge = TeachingAssistantVoiceBridge(stt=FakeSTT(), brain=FakeBrain())
    session = RealtimeTeachingSession(microphone=FakeMic(audio), voice_bridge=bridge)
    events = list(session.run(max_turns=1))
    assert events[3].turn is not None
    assert not hasattr(events[3].turn, "executed_actions")
