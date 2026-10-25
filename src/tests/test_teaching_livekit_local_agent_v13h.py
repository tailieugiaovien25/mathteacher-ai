import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_kernel.teaching_livekit_local_agent import LocalLiveKitAgentConfig, LocalLiveKitAgentSession  # noqa: E402


class _FakeSTTResult:
    text = "mở hoạt động khởi động"


class _FakeSTT:
    def transcribe(self, path, *, language="vi"):
        del path, language
        return _FakeSTTResult()


class _FakeAgent:
    def __init__(self):
        self.speaking = False
        self.interrupted = 0
        self.transcripts = []

    def is_speaking(self):
        return self.speaking

    async def interrupt(self):
        self.interrupted += 1
        self.speaking = False
        return None

    async def respond(self, transcript):
        self.transcripts.append(transcript)
        self.speaking = True
        class E:
            kind = "audio_chunk"
            audio_chunk = b"audio"
        yield E()
        self.speaking = False
        class D:
            kind = "response_done"
            audio_chunk = b""
        yield D()


def test_local_session_collects_turn_and_starts_response(monkeypatch, tmp_path):
    agent = _FakeAgent()
    sess = LocalLiveKitAgentSession(agent=agent, config=LocalLiveKitAgentConfig(output_dir=tmp_path, silence_timeout_ms=60, min_utterance_ms=1))
    sess._stt = _FakeSTT()

    async def run():
        # 16-bit mono 16kHz silence+speech blocks; this is enough for the dependency-free VAD.
        speech = (b"\x00\x40" * 480).strip()  # non-zero PCM
        silence = b"\x00\x00" * 480
        await sess.consume_frame(speech, block_ms=30)
        await sess.consume_frame(silence, block_ms=60)
        await asyncio.sleep(0.01)
        assert agent.transcripts == ["mở hoạt động khởi động"]

    asyncio.run(run())


def test_barge_in_interrupts_active_agent():
    agent = _FakeAgent()
    agent.speaking = True
    sess = LocalLiveKitAgentSession(agent=agent, config=LocalLiveKitAgentConfig())

    async def run():
        speech = b"\x00\x60" * 480
        await sess.consume_frame(speech, block_ms=30)
        assert agent.interrupted == 1

    asyncio.run(run())
