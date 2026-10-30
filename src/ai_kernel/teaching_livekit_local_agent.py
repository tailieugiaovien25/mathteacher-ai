from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
import tempfile
import time
import wave
from typing import Awaitable, Callable

from .teaching_realtime import EnergyVoiceActivityDetector, RealtimeVoiceConfig
from .teaching_realtime_agent import RealtimeAgentEvent, RealtimeVoiceAgent
from .teaching_voice import FasterWhisperSTT


@dataclass(frozen=True)
class LocalLiveKitAgentConfig:
    sample_rate: int = 16_000
    channels: int = 1
    sample_width_bytes: int = 2
    block_duration_ms: int = 30
    silence_timeout_ms: int = 700
    max_utterance_ms: int = 15_000
    min_utterance_ms: int = 240
    energy_threshold: float = 0.015
    output_dir: str | Path | None = None
    stt_model: str = "small"
    stt_device: str = "auto"
    stt_compute_type: str = "int8"


@dataclass
class LocalLiveKitAgentSession:
    """Bridge raw LiveKit PCM frames to local STT -> LLM -> TTS with barge-in."""

    agent: RealtimeVoiceAgent
    config: LocalLiveKitAgentConfig = field(default_factory=LocalLiveKitAgentConfig)
    on_audio_chunk: Callable[[bytes], Awaitable[None]] | None = None
    on_event: Callable[[RealtimeAgentEvent], Awaitable[None]] | None = None

    _vad: EnergyVoiceActivityDetector = field(init=False)
    _frames: list[bytes] = field(default_factory=list, init=False)
    _started: bool = field(default=False, init=False)
    _elapsed_ms: int = field(default=0, init=False)
    _response_task: asyncio.Task[None] | None = field(default=None, init=False)
    _stt: FasterWhisperSTT | None = field(default=None, init=False)
    _teacher_override: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._vad = EnergyVoiceActivityDetector(
            threshold=self.config.energy_threshold,
            silence_timeout_ms=self.config.silence_timeout_ms,
        )

    @property
    def teacher_override(self) -> bool:
        return self._teacher_override

    async def set_teacher_override(self, active: bool) -> None:
        self._teacher_override = bool(active)
        if active:
            await self.stop_speaking()

    async def stop_speaking(self) -> None:
        if self.agent.is_speaking():
            await self.agent.interrupt()
        task = self._response_task
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        self._response_task = None

    async def consume_frame(self, pcm16: bytes, *, block_ms: int | None = None) -> None:
        duration_ms = max(1, int(block_ms or self.config.block_duration_ms))
        active, ended = self._vad.feed(pcm16, block_ms=duration_ms)

        # Barge-in: teacher speech takes precedence over assistant speech.
        if active and self.agent.is_speaking():
            await self.stop_speaking()

        if self._teacher_override:
            self._reset_capture()
            return

        # Silence before the first voiced frame must not consume the utterance
        # time budget; otherwise a quiet room can cause the next word to be cut.
        if active and not self._started:
            self._started = True
            self._elapsed_ms = 0
        if not self._started:
            return

        self._frames.append(bytes(pcm16))
        self._elapsed_ms = min(self.config.max_utterance_ms, self._elapsed_ms + duration_ms)

        if ended or self._elapsed_ms >= self.config.max_utterance_ms:
            frames = tuple(self._frames)
            self._reset_capture()
            if self._duration_ms(frames) >= self.config.min_utterance_ms:
                await self._handle_utterance(frames)

    async def flush(self) -> None:
        if self._frames:
            frames = tuple(self._frames)
            self._reset_capture()
            if self._duration_ms(frames) >= self.config.min_utterance_ms:
                await self._handle_utterance(frames)

    async def _handle_utterance(self, frames: tuple[bytes, ...]) -> None:
        audio_path = self._write_wav(frames)
        stt = self._stt_instance()
        result = await asyncio.to_thread(stt.transcribe, audio_path, language="vi")
        if not result.text.strip():
            return

        # A new teacher turn always preempts the previous response.
        if self.agent.is_speaking():
            await self.stop_speaking()

        if self._response_task is not None and not self._response_task.done():
            await asyncio.gather(self._response_task, return_exceptions=True)

        self._response_task = asyncio.create_task(self._respond(result.text.strip()))

    async def _respond(self, transcript: str) -> None:
        try:
            async for event in self.agent.respond(transcript):
                if self.on_event is not None:
                    await self.on_event(event)
                if event.kind == "audio_chunk" and self.on_audio_chunk is not None:
                    await self.on_audio_chunk(event.audio_chunk)
        except asyncio.CancelledError:
            raise

    def _stt_instance(self) -> FasterWhisperSTT:
        if self._stt is None:
            self._stt = FasterWhisperSTT(
                model_size=self.config.stt_model,
                device=self.config.stt_device,
                compute_type=self.config.stt_compute_type,
            )
        return self._stt

    def _write_wav(self, frames: tuple[bytes, ...]) -> Path:
        output_dir = Path(self.config.output_dir) if self.config.output_dir else Path(tempfile.gettempdir()) / "mathteacher_ai_livekit_voice"
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"turn_{time.time_ns()}.wav"
        with wave.open(str(output), "wb") as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(self.config.sample_width_bytes)
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(b"".join(frames))
        return output

    def _reset_capture(self) -> None:
        self._vad = EnergyVoiceActivityDetector(
            threshold=self.config.energy_threshold,
            silence_timeout_ms=self.config.silence_timeout_ms,
        )
        self._frames.clear()
        self._started = False
        self._elapsed_ms = 0

    def _duration_ms(self, frames: tuple[bytes, ...]) -> int:
        samples = sum(len(frame) for frame in frames) // self.config.sample_width_bytes
        return int(samples * 1000 / max(1, self.config.sample_rate))


__all__ = ["LocalLiveKitAgentConfig", "LocalLiveKitAgentSession"]
