from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import tempfile
import time
import wave
from typing import Callable, Protocol

from .teaching_voice import TeachingAssistantVoiceBridge, TeachingVoiceTurn


class AudioInputProvider(Protocol):
    def record_utterance(self, *, config: "RealtimeVoiceConfig") -> Path: ...


@dataclass(frozen=True)
class RealtimeVoiceConfig:
    sample_rate: int = 16_000
    channels: int = 1
    sample_width_bytes: int = 2
    block_duration_ms: int = 30
    silence_timeout_ms: int = 900
    max_utterance_ms: int = 15_000
    min_utterance_ms: int = 240
    energy_threshold: float = 0.015
    pre_roll_ms: int = 180
    output_dir: str | Path | None = None

    @property
    def frames_per_block(self) -> int:
        return max(1, int(self.sample_rate * self.block_duration_ms / 1000))


class EnergyVoiceActivityDetector:
    """Small dependency-free RMS VAD used only for turn segmentation.

    It intentionally does not try to transcribe speech. Audio is segmented first,
    then the existing local STT adapter handles transcription.
    """

    def __init__(self, *, threshold: float, silence_timeout_ms: int) -> None:
        self.threshold = max(0.0001, float(threshold))
        self.silence_timeout_ms = max(60, int(silence_timeout_ms))
        self.silence_ms = 0
        self.started = False

    @staticmethod
    def rms(pcm16: bytes) -> float:
        if not pcm16:
            return 0.0
        sample_count = len(pcm16) // 2
        total = 0.0
        for index in range(sample_count):
            value = int.from_bytes(pcm16[index * 2:index * 2 + 2], "little", signed=True)
            normalized = value / 32768.0
            total += normalized * normalized
        return math.sqrt(total / max(1, sample_count))

    def feed(self, pcm16: bytes, *, block_ms: int) -> tuple[bool, bool]:
        active = self.rms(pcm16) >= self.threshold
        if active:
            self.started = True
            self.silence_ms = 0
        elif self.started:
            self.silence_ms += block_ms
        ended = self.started and self.silence_ms >= self.silence_timeout_ms
        return active, ended


class SoundDeviceMicrophone:
    """Optional local microphone capture using sounddevice.

    Imported lazily so the rest of MathTeacher AI remains usable without a
    microphone package installed. Recording is turn-based using a simple RMS VAD.
    """

    def __init__(self, *, audio_dir: str | Path | None = None) -> None:
        self.audio_dir = Path(audio_dir) if audio_dir else Path(tempfile.gettempdir()) / "mathteacher_ai_voice"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def _require_sounddevice(self):
        try:
            import sounddevice as sd  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Chưa cài sounddevice. Hãy cài dependency microphone local trước khi dùng realtime voice."
            ) from exc
        return sd

    def record_utterance(self, *, config: RealtimeVoiceConfig) -> Path:
        sd = self._require_sounddevice()
        block_frames = config.frames_per_block
        detector = EnergyVoiceActivityDetector(
            threshold=config.energy_threshold,
            silence_timeout_ms=config.silence_timeout_ms,
        )
        pre_roll_blocks = max(0, int(config.pre_roll_ms / config.block_duration_ms))
        max_blocks = max(1, int(config.max_utterance_ms / config.block_duration_ms))
        min_blocks = max(1, int(config.min_utterance_ms / config.block_duration_ms))
        pre_roll: list[bytes] = []
        captured: list[bytes] = []

        stream = sd.RawInputStream(
            samplerate=config.sample_rate,
            blocksize=block_frames,
            channels=config.channels,
            dtype="int16",
        )
        try:
            with stream:
                for _ in range(max_blocks):
                    block, overflowed = stream.read(block_frames)
                    del overflowed  # non-fatal for a local prototype
                    raw = bytes(block)
                    pre_roll.append(raw)
                    if len(pre_roll) > pre_roll_blocks:
                        pre_roll.pop(0)
                    _, ended = detector.feed(raw, block_ms=config.block_duration_ms)
                    if detector.started and not captured:
                        captured.extend(pre_roll)
                    elif detector.started:
                        captured.append(raw)
                    if ended and len(captured) >= min_blocks:
                        break
            if len(captured) < min_blocks:
                raise RuntimeError("Không thu được một lượt nói đủ dài từ microphone.")
        finally:
            try:
                stream.close()
            except Exception:
                pass

        output_dir = Path(config.output_dir) if config.output_dir else self.audio_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"turn_{int(time.time() * 1000)}.wav"
        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(config.channels)
            wf.setsampwidth(config.sample_width_bytes)
            wf.setframerate(config.sample_rate)
            wf.writeframes(b"".join(captured))
        return output_path


@dataclass(frozen=True)
class RealtimeTurnEvent:
    state: str
    turn: TeachingVoiceTurn | None = None
    audio_path: Path | None = None
    error: str | None = None


class RealtimeTeachingSession:
    """Turn-based realtime voice session.

    It processes one microphone utterance at a time and exposes explicit state
    events. Teacher control is kept outside this class; a caller may stop the
    session at any point. No classroom tool is executed here.
    """

    def __init__(
        self,
        *,
        microphone: AudioInputProvider,
        voice_bridge: TeachingAssistantVoiceBridge,
        config: RealtimeVoiceConfig | None = None,
        should_continue: Callable[[], bool] | None = None,
    ) -> None:
        self.microphone = microphone
        self.voice_bridge = voice_bridge
        self.config = config or RealtimeVoiceConfig()
        self.should_continue = should_continue or (lambda: True)
        self.running = False

    def stop(self) -> None:
        self.running = False

    def run(self, *, max_turns: int | None = None):
        self.running = True
        yield RealtimeTurnEvent(state="session_started")
        turns = 0
        while self.running and self.should_continue():
            if max_turns is not None and turns >= max_turns:
                break
            try:
                yield RealtimeTurnEvent(state="listening")
                audio_path = self.microphone.record_utterance(config=self.config)
                yield RealtimeTurnEvent(state="processing", audio_path=audio_path)
                output_path = self._tts_output_for(audio_path)
                turn = self.voice_bridge.process_audio(audio_path, output_path=output_path if self.voice_bridge.tts else None)
                turns += 1
                yield RealtimeTurnEvent(
                    state="turn_completed",
                    turn=turn,
                    audio_path=audio_path,
                )
            except KeyboardInterrupt:
                self.running = False
                yield RealtimeTurnEvent(state="stopped")
                break
            except Exception as exc:
                yield RealtimeTurnEvent(state="error", error=str(exc))
                break
        self.running = False
        yield RealtimeTurnEvent(state="session_stopped")

    @staticmethod
    def _tts_output_for(audio_path: Path) -> Path:
        return audio_path.with_name(audio_path.stem + "_reply.wav")


__all__ = [
    "AudioInputProvider",
    "EnergyVoiceActivityDetector",
    "RealtimeTeachingSession",
    "RealtimeTurnEvent",
    "RealtimeVoiceConfig",
    "SoundDeviceMicrophone",
]
