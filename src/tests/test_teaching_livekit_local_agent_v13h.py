import asyncio
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_kernel.teaching_livekit_local_agent import LocalLiveKitAgentConfig, LocalLiveKitAgentSession  # noqa: E402


class _FakeSTTResult:
    text = "mở hoạt động khởi động"


class _FakeSTT:
    def __init__(self):
        self.duration_ms = 0

    def transcribe(self, path, *, language="vi"):
        del language
        with wave.open(str(path), "rb") as audio:
            self.duration_ms = int(audio.getnframes() * 1000 / audio.getframerate())
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


def test_silence_before_speech_does_not_consume_utterance_budget(tmp_path):
    agent = _FakeAgent()
    config = LocalLiveKitAgentConfig(
        output_dir=tmp_path,
        block_duration_ms=30,
        silence_timeout_ms=60,
        max_utterance_ms=90,
        min_utterance_ms=30,
    )
    sess = LocalLiveKitAgentSession(agent=agent, config=config)
    stt = _FakeSTT()
    sess._stt = stt

    async def run():
        silence = b"\x00\x00" * 480
        speech = b"\x00\x40" * 480
        for _ in range(8):
            await sess.consume_frame(silence, block_ms=30)
        assert sess._elapsed_ms == 0
        await sess.consume_frame(speech, block_ms=30)
        await sess.consume_frame(silence, block_ms=30)
        await sess.consume_frame(silence, block_ms=30)
        await asyncio.sleep(0.01)
        assert agent.transcripts == ["mở hoạt động khởi động"]
        # Six pre-roll frames (180 ms), the voiced frame and trailing silence
        # are retained in the WAV; only voiced/post-onset time counts toward max.
        assert stt.duration_ms >= 240

    asyncio.run(run())


def test_zero_pre_roll_keeps_the_first_voiced_frame(tmp_path):
    agent = _FakeAgent()
    config = LocalLiveKitAgentConfig(
        output_dir=tmp_path,
        pre_roll_ms=0,
        silence_timeout_ms=60,
        min_utterance_ms=1,
    )
    sess = LocalLiveKitAgentSession(agent=agent, config=config)
    stt = _FakeSTT()
    sess._stt = stt

    async def run():
        speech = b"\\x00\\x40" * 480
        silence = b"\\x00\\x00" * 480
        await sess.consume_frame(speech, block_ms=30)
        await sess.consume_frame(silence, block_ms=60)
        await asyncio.sleep(0.01)
        assert agent.transcripts == ["mở hoạt động khởi động"]
        assert stt.duration_ms >= 90

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
