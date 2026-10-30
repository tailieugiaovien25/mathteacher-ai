import asyncio
import json
from pathlib import Path
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_kernel.teaching_realtime_agent import (  # noqa: E402
    AIKernelStreamingBrain,
    OllamaStreamingBrain,
    RealtimeAgentEvent,
    RealtimeVoiceAgent,
    RealtimeVoiceAgentConfig,
    build_livekit_agent_descriptor,
)


class _FakeResponse:
    def __init__(self, lines):
        self._lines = iter(lines)
        self.closed = False

    def readline(self):
        try:
            return next(self._lines)
        except StopIteration:
            return b""

    def close(self):
        self.closed = True


class _FakeBrain:
    async def stream_response(self, *, transcript, system_prompt, history=()):
        del system_prompt, history
        for piece in ["Xin ", "chào. ", "Chúng ta bắt đầu nhé."]:
            await asyncio.sleep(0)
            yield piece


class _FakeTTS:
    sample_rate = 48000

    async def stream_audio(self, text):
        del text
        await asyncio.sleep(0)
        yield b"audio-1"
        yield b"audio-2"


def test_ollama_jsonl_stream(monkeypatch):
    lines = [
        (json.dumps({"message": {"content": "Xin "}}) + "\n").encode(),
        (json.dumps({"message": {"content": "chào."}, "done": True}) + "\n").encode(),
    ]
    fake = _FakeResponse(lines)
    brain = OllamaStreamingBrain(opener=lambda *args, **kwargs: fake)

    async def run():
        return [
            part
            async for part in brain.stream_response(
                transcript="Xin chào",
                system_prompt="trợ giảng",
            )
        ]

    assert asyncio.run(run()) == ["Xin ", "chào."]


def test_agent_streams_and_can_be_interrupted():
    agent = RealtimeVoiceAgent(_FakeBrain(), _FakeTTS(), RealtimeVoiceAgentConfig(min_tts_chars=1))

    async def run():
        events = [event async for event in agent.respond("Xin chào")]
        kinds = [event.kind for event in events]
        assert "thinking" in kinds
        assert "text_delta" in kinds
        assert "audio_chunk" in kinds
        assert kinds[-1] == "response_done"

    asyncio.run(run())


def test_barge_in_cancels_active_response():
    class SlowBrain:
        async def stream_response(self, *, transcript, system_prompt, history=()):
            del transcript, system_prompt, history
            while True:
                await asyncio.sleep(0.01)
                yield "đang nói... "

    async def run():
        agent = RealtimeVoiceAgent(SlowBrain(), _FakeTTS())
        task = asyncio.create_task(consume(agent.respond("hãy kể tiếp")))
        await asyncio.sleep(0.03)
        event = await agent.interrupt()
        result = await task
        assert event.kind == "interrupted"
        assert agent.is_speaking() is False
        assert result[0].kind == "thinking"

    async def consume(events):
        seen = []
        async for ev in events:
            seen.append(ev)
        return seen

    asyncio.run(run())


def test_livekit_descriptor_is_local_first():
    descriptor = build_livekit_agent_descriptor()
    assert descriptor.self_hosted is True
    assert descriptor.allow_barge_in is True
    assert descriptor.local_llm.startswith("ollama:")
    assert descriptor.local_stt.startswith("faster-whisper:")
    assert descriptor.local_tts.startswith("zerotts:")

def test_ai_kernel_streaming_brain_surfaces_provider_errors():
    class BrokenService:
        def stream(self, **kwargs):
            del kwargs

            def broken_stream():
                raise RuntimeError("synthetic provider failure")
                yield "unreachable"

            return broken_stream()

    brain = AIKernelStreamingBrain(service=BrokenService())

    async def run():
        with pytest.raises(RuntimeError, match="synthetic provider failure"):
            async for _ in brain.stream_response(
                transcript="Kiểm tra",
                system_prompt="Trợ giảng",
            ):
                pass

    asyncio.run(run())

