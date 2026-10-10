import json
from pathlib import Path

import pytest

from ai_kernel.teaching_voice import (
    CommandTTSAdapter,
    STTResult,
    TeachingAssistantVoiceBridge,
    TeachingVoiceConfig,
)


class FakeSTT:
    def transcribe(self, audio_path, *, language="vi"):
        return STTResult(text="Trợ giảng, hãy giới thiệu hoạt động hôm nay.", language=language, provider="fake")


class FakeBrain:
    def respond(self, *, transcript, system_prompt, history=()):
        assert "tiếng Việt" in system_prompt
        return f"Mình sẽ giới thiệu hoạt động dựa trên yêu cầu: {transcript}"


def test_voice_bridge_runs_stt_to_brain_without_tts(tmp_path):
    audio = tmp_path / "input.wav"
    audio.write_bytes(b"fake")
    bridge = TeachingAssistantVoiceBridge(stt=FakeSTT(), brain=FakeBrain(), config=TeachingVoiceConfig())
    turn = bridge.process_audio(audio)
    assert turn.transcript.text.startswith("Trợ giảng")
    assert "giới thiệu hoạt động" in turn.response_text


def test_voice_bridge_requires_output_path_when_tts_is_configured(tmp_path):
    class FakeTTS:
        def synthesize(self, text, *, output_path):
            return Path(output_path)

    audio = tmp_path / "input.wav"
    audio.write_bytes(b"fake")
    bridge = TeachingAssistantVoiceBridge(stt=FakeSTT(), brain=FakeBrain(), tts=FakeTTS())
    with pytest.raises(ValueError):
        bridge.process_audio(audio)


def test_command_tts_validates_placeholders():
    with pytest.raises(ValueError):
        CommandTTSAdapter("echo {text}")


def test_ollama_payload_contract(monkeypatch):
    import ai_kernel.teaching_voice as voice

    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"message": {"content": "Được, chúng ta bắt đầu."}}).encode("utf-8")

    def fake_open(request, timeout=None):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    brain = voice.OllamaTeachingBrain(opener=fake_open)
    result = brain.respond(transcript="Bắt đầu tiết học.", system_prompt="Trả lời tiếng Việt.")
    assert result == "Được, chúng ta bắt đầu."
    assert captured["url"].endswith("/api/chat")
    assert captured["body"]["model"] == "qwen3:8b"
    assert captured["body"]["stream"] is False
    assert captured["body"]["messages"][-1]["content"] == "Bắt đầu tiết học."
