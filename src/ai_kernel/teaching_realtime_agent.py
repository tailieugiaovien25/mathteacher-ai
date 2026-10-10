from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Mapping, Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .contracts import AIOwnership, AIActionClass
from .service import AIKernelService


class StreamingBrain(Protocol):
    async def stream_response(
        self,
        *,
        transcript: str,
        system_prompt: str,
        history: Sequence[Mapping[str, str]] = (),
    ) -> AsyncIterator[str]: ...


class StreamingTTS(Protocol):
    sample_rate: int

    async def stream_audio(self, text: str) -> AsyncIterator[bytes]: ...


@dataclass(frozen=True)
class RealtimeVoiceAgentConfig:
    system_prompt: str = (
        "Báº¡n lÃ  Trá»£ giáº£ng ToÃ¡n THCS cá»§a MathTeacher AI. "
        "Tráº£ lá»i báº±ng tiáº¿ng Viá»‡t, rÃµ rÃ ng, tá»± nhiÃªn, phÃ¹ há»£p vá»›i lá»›p há»c. "
        "KhÃ´ng tá»± Ã½ thá»±c hiá»‡n hÃ nh Ä‘á»™ng ká»¹ thuáº­t. Náº¿u cáº§n hÃ nh Ä‘á»™ng, chá»‰ táº¡o Ä‘á» xuáº¥t "
        "Ä‘á»ƒ Teaching Assistant Controller xá»­ lÃ½."
    )
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:8b"
    request_timeout_s: float = 60.0
    min_tts_chars: int = 24


class AIKernelStreamingBrain:
    """Realtime streaming brain routed through the ADMIN-controlled AI Kernel."""

    def __init__(self, service: AIKernelService | None = None) -> None:
        self.service = service or AIKernelService()

    async def stream_response(
        self,
        *,
        transcript: str,
        system_prompt: str,
        history: Sequence[Mapping[str, str]] = (),
    ) -> AsyncIterator[str]:
        history_lines = []
        for item in history[-8:]:
            role = item.get("role", "unknown")
            content = item.get("content", "")
            history_lines.append(f"{role}: {content}")

        history_text = "\n".join(history_lines) if history_lines else "(no history)"

        prompt = (
            system_prompt
            + "\n\nRecent conversation:\n"
            + history_text
            + "\n\nUser says:\n"
            + transcript
            + "\n\nRespond directly in Vietnamese."
        )

        stream = await asyncio.to_thread(
            self.service.stream,
            task_id="teaching_assistant_voice_stream",
            prompt=prompt,
            capabilities=("general", "vietnamese", "mathematics"),
            owner=AIOwnership.USER,
            action=AIActionClass.ADVISORY,
            metadata={
                "channel": "voice",
                "interface": "teaching_assistant",
                "mutating": "false",
                "streaming": "true",
            },
            skill_id="classroom.assistant",
        )

        queue: asyncio.Queue[str | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def producer() -> None:
            try:
                for chunk in stream:
                    if chunk:
                        asyncio.run_coroutine_threadsafe(
                            queue.put(str(chunk)),
                            loop,
                        ).result()
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()

        task = asyncio.create_task(asyncio.to_thread(producer))
        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                yield chunk
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

class OllamaStreamingBrain:
    """Local Ollama chat streaming adapter.

    The adapter emits content deltas from Ollama's newline-delimited JSON stream.
    It never executes classroom actions.
    """

    def __init__(
        self,
        config: RealtimeVoiceAgentConfig | None = None,
        *,
        opener=urlopen,
    ) -> None:
        self.config = config or RealtimeVoiceAgentConfig()
        self._opener = opener

    def _open_stream(self, payload: bytes):
        request = Request(
            self.config.ollama_base_url.rstrip("/") + "/api/chat",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            return self._opener(request, timeout=self.config.request_timeout_s)
        except HTTPError as exc:
            raise RuntimeError(f"Ollama HTTP error: {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError("KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c Ollama local.") from exc
        except OSError as exc:
            raise RuntimeError("KhÃ´ng má»Ÿ Ä‘Æ°á»£c luá»“ng Ollama local.") from exc

    async def stream_response(
        self,
        *,
        transcript: str,
        system_prompt: str,
        history: Sequence[Mapping[str, str]] = (),
    ) -> AsyncIterator[str]:
        messages: list[Mapping[str, str]] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": transcript})
        payload = json.dumps(
            {"model": self.config.ollama_model, "messages": messages, "stream": True}
        ).encode("utf-8")

        response = await asyncio.to_thread(self._open_stream, payload)
        try:
            while True:
                line = await asyncio.to_thread(response.readline)
                if not line:
                    break
                try:
                    item = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                content = ((item.get("message") or {}).get("content") or "")
                if content:
                    yield content
                if item.get("done") is True:
                    break
        finally:
            await asyncio.to_thread(response.close)


class ZeroTTSStreamingAdapter:
    """Local Vietnamese TTS adapter backed by ZeroTTS.

    The optional dependency is loaded lazily. Audio chunks are PCM float32
    little-endian bytes so a transport layer can publish them incrementally.
    """

    sample_rate = 48_000

    def __init__(self, *, model_name: str = "zeroweight-ai/ZeroTTS", voice: str | None = "maichi") -> None:
        self.model_name = model_name
        self.voice = voice
        self._tts = None

    def _ensure(self):
        if self._tts is None:
            try:
                from zerotts import ZeroTTS  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "ChÆ°a cÃ i ZeroTTS. CÃ i `zerotts` Ä‘á»ƒ báº­t TTS tiáº¿ng Viá»‡t local streaming."
                ) from exc
            self._tts = ZeroTTS.from_pretrained(self.model_name)
        return self._tts

    async def stream_audio(self, text: str) -> AsyncIterator[bytes]:
        tts = self._ensure()
        kwargs = {"voice": self.voice} if self.voice else {}
        stream = await asyncio.to_thread(lambda: tts.synthesize_stream(text, **kwargs))
        try:
            # The ZeroTTS iterable itself is synchronous; consume it off the event loop.
            queue: asyncio.Queue[bytes | None] = asyncio.Queue()

            def producer() -> None:
                try:
                    for chunk in stream:
                        data = getattr(chunk, "tobytes", lambda: bytes(chunk))()
                        asyncio.run_coroutine_threadsafe(queue.put(data), loop).result()
                finally:
                    asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()

            loop = asyncio.get_running_loop()
            task = asyncio.create_task(asyncio.to_thread(producer))
            try:
                while True:
                    item = await queue.get()
                    if item is None:
                        break
                    yield item
            finally:
                if not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
        finally:
            del stream


@dataclass(frozen=True)
class RealtimeAgentEvent:
    kind: str
    text: str = ""
    audio_chunk: bytes = b""
    error: str | None = None


@dataclass
class RealtimeVoiceAgent:
    """Provider-agnostic realtime voice controller with barge-in.

    Audio transport and STT turn detection live outside this class. This layer
    accepts finalized/interim transcript events and streams local LLM/TTS output.
    Interrupting cancels the active response immediately.
    """

    brain: StreamingBrain
    tts: StreamingTTS
    config: RealtimeVoiceAgentConfig = field(default_factory=RealtimeVoiceAgentConfig)
    history: list[Mapping[str, str]] = field(default_factory=list)

    _response_task: asyncio.Task[None] | None = field(default=None, init=False, repr=False)
    _active_queue: asyncio.Queue[RealtimeAgentEvent] | None = field(default=None, init=False, repr=False)
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event, init=False, repr=False)

    def is_speaking(self) -> bool:
        return self._response_task is not None and not self._response_task.done()

    async def interrupt(self) -> RealtimeAgentEvent:
        self._cancel_event.set()
        task = self._response_task
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        self._response_task = None
        queue = self._active_queue
        if queue is not None:
            await queue.put(RealtimeAgentEvent(kind="interrupted"))
        return RealtimeAgentEvent(kind="interrupted")

    async def respond(self, transcript: str) -> AsyncIterator[RealtimeAgentEvent]:
        cleaned = transcript.strip()
        if not cleaned:
            yield RealtimeAgentEvent(kind="ignored")
            return

        if self.is_speaking():
            await self.interrupt()

        self._cancel_event = asyncio.Event()
        queue: asyncio.Queue[RealtimeAgentEvent] = asyncio.Queue()
        self._active_queue = queue
        self._response_task = asyncio.create_task(self._run_response(cleaned, queue))

        while True:
            event = await queue.get()
            yield event
            if event.kind in {"response_done", "interrupted", "error"}:
                break

        self._active_queue = None

    async def _run_response(self, transcript: str, queue: asyncio.Queue[RealtimeAgentEvent]) -> None:
        full_text = ""
        tts_buffer = ""
        try:
            await queue.put(RealtimeAgentEvent(kind="thinking"))
            async for delta in self.brain.stream_response(
                transcript=transcript,
                system_prompt=self.config.system_prompt,
                history=tuple(self.history[-8:]),
            ):
                if self._cancel_event.is_set():
                    await queue.put(RealtimeAgentEvent(kind="interrupted"))
                    return
                if not delta:
                    continue
                full_text += delta
                tts_buffer += delta
                await queue.put(RealtimeAgentEvent(kind="text_delta", text=delta))

                # Stream small but speakable chunks. Prefer punctuation boundaries.
                should_flush = (
                    len(tts_buffer) >= self.config.min_tts_chars
                    and tts_buffer.rstrip().endswith((".", "!", "?", "â€¦", ":", ";", ","))
                )
                if should_flush:
                    await self._speak_chunk(tts_buffer.strip(), queue)
                    tts_buffer = ""

            if self._cancel_event.is_set():
                await queue.put(RealtimeAgentEvent(kind="interrupted"))
                return
            if tts_buffer.strip():
                await self._speak_chunk(tts_buffer.strip(), queue)

            self.history.append({"role": "user", "content": transcript})
            self.history.append({"role": "assistant", "content": full_text.strip()})
            await queue.put(RealtimeAgentEvent(kind="response_done", text=full_text.strip()))
        except asyncio.CancelledError:
            # Caller intentionally interrupted the speech.
            raise
        except Exception as exc:
            await queue.put(RealtimeAgentEvent(kind="error", error=str(exc)))

    async def _speak_chunk(self, text: str, queue: asyncio.Queue[RealtimeAgentEvent]) -> None:
        if not text:
            return
        await queue.put(RealtimeAgentEvent(kind="speaking", text=text))
        async for chunk in self.tts.stream_audio(text):
            if self._cancel_event.is_set():
                return
            await queue.put(RealtimeAgentEvent(kind="audio_chunk", audio_chunk=chunk))


@dataclass(frozen=True)
class LiveKitAgentRuntimeDescriptor:
    """Deployment metadata for the optional LiveKit Agents worker."""

    server_url: str
    room_name: str
    agent_identity: str = "mathteacher-ai-teaching-assistant"
    language: str = "vi-VN"
    local_llm: str = "ollama:qwen3:8b"
    local_stt: str = "faster-whisper:small"
    local_tts: str = "zerotts:maichi"
    allow_barge_in: bool = True
    self_hosted: bool = True


def build_livekit_agent_descriptor() -> LiveKitAgentRuntimeDescriptor:
    return LiveKitAgentRuntimeDescriptor(
        server_url=os.environ.get("MATHTEACHER_LIVEKIT_URL", "ws://127.0.0.1:7880"),
        room_name=os.environ.get(
            "MATHTEACHER_LIVEKIT_ROOM", "mathteacher-ai-teaching-assistant"
        ),
        agent_identity=os.environ.get(
            "MATHTEACHER_LIVEKIT_AGENT_ID", "mathteacher-ai-teaching-assistant"
        ),
        local_llm=os.environ.get("MATHTEACHER_AI_LOCAL_LLM", "ollama:qwen3:8b"),
        local_stt=os.environ.get("MATHTEACHER_AI_LOCAL_STT", "faster-whisper:small"),
        local_tts=os.environ.get("MATHTEACHER_AI_LOCAL_TTS", "zerotts:maichi"),
    )


__all__ = [
    "LiveKitAgentRuntimeDescriptor",
    "OllamaStreamingBrain",
    "RealtimeAgentEvent",
    "RealtimeVoiceAgent",
    "RealtimeVoiceAgentConfig",
    "StreamingBrain",
    "StreamingTTS",
    "ZeroTTSStreamingAdapter",
    "build_livekit_agent_descriptor",
]
