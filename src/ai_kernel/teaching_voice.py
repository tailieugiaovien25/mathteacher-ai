from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import shlex
import shlex
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping, Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SpeechToTextProvider(Protocol):
    def transcribe(self, audio_path: str | Path, *, language: str = "vi") -> "STTResult": ...


class TeachingBrain(Protocol):
    def respond(self, *, transcript: str, system_prompt: str, history: Sequence[Mapping[str, str]] = ()) -> str: ...


class TextToSpeechProvider(Protocol):
    def synthesize(self, text: str, *, output_path: str | Path) -> Path: ...


@dataclass(frozen=True)
class STTResult:
    text: str
    language: str = "vi"
    confidence: float | None = None
    provider: str = "unknown"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TeachingVoiceConfig:
    system_prompt: str = (
        "\u0042\u1ea1n l\u00e0 Tr\u1ee3 gi\u1ea3ng To\u00e1n THCS c\u1ee7a MathTeacher AI. "
        "\u0110\u1ed1i t\u01b0\u1ee3ng giao ti\u1ebfp m\u1eb7c \u0111\u1ecbnh l\u00e0 gi\u00e1o vi\u00ean; "
        "h\u00e3y g\u1ecdi ng\u01b0\u1eddi d\u00f9ng l\u00e0 th\u1ea7y/c\u00f4 v\u00e0 x\u01b0ng em. "
        "Kh\u00f4ng t\u1ef1 nh\u1eadn m\u00ecnh l\u00e0 gi\u00e1o vi\u00ean. "
        "Tr\u1ea3 l\u1eddi ng\u1eafn g\u1ecdn, r\u00f5 r\u00e0ng, th\u00e2n thi\u1ec7n, ph\u00f9 h\u1ee3p v\u1edbi gi\u00e1o vi\u00ean To\u00e1n THCS. "
        "H\u1ed7 tr\u1ee3 so\u1ea1n b\u00e0i, gi\u1ea3i th\u00edch To\u00e1n, t\u1ed5 ch\u1ee9c ho\u1ea1t \u0111\u1ed9ng d\u1ea1y h\u1ecdc v\u00e0 ph\u1ea3n h\u1ed3i s\u01b0 ph\u1ea1m. "
        "Kh\u00f4ng t\u1ef1 \u00fd th\u1ef1c hi\u1ec7n h\u00e0nh \u0111\u1ed9ng k\u1ef9 thu\u1eadt, thay \u0111\u1ed5i h\u1ec7 th\u1ed1ng, b\u00e0i gi\u1ea3ng ho\u1eb7c d\u1eef li\u1ec7u. "
        "Khi c\u1ea7n h\u00e0nh \u0111\u1ed9ng, ch\u1ec9 \u0111\u1ec1 xu\u1ea5t \u0111\u1ec3 Classroom/Approval layer x\u1eed l\u00fd."
    )
    mode: str = "teacher"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:0.6b"
    request_timeout_s: float = 60.0


class OllamaTeachingBrain:
    """Minimal local Ollama chat adapter; no cloud dependency."""

    def __init__(self, config: TeachingVoiceConfig | None = None, *, opener: Callable[..., Any] | None = None) -> None:
        self.config = config or TeachingVoiceConfig()
        self._opener = opener or urlopen

    def health(self) -> bool:
        request = Request(
            self.config.ollama_base_url.rstrip("/") + "/api/tags",
            method="GET",
            headers={"Accept": "application/json"},
        )
        try:
            with self._opener(request, timeout=self.config.request_timeout_s) as response:
                return int(response.status) == 200
        except (OSError, HTTPError, URLError):
            return False

    def respond(self, *, transcript: str, system_prompt: str, history: Sequence[Mapping[str, str]] = ()) -> str:
        messages: list[Mapping[str, str]] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": transcript})
        payload = json.dumps({
            "model": self.config.ollama_model,
            "messages": messages,
            "stream": False,
        }).encode("utf-8")
        request = Request(
            self.config.ollama_base_url.rstrip("/") + "/api/chat",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with self._opener(request, timeout=self.config.request_timeout_s) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"Ollama HTTP error: {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError("KhÃƒÂ´ng kÃ¡ÂºÂ¿t nÃ¡Â»â€˜i Ã„â€˜Ã†Â°Ã¡Â»Â£c Ollama local.") from exc
        except OSError as exc:
            raise RuntimeError("KhÃƒÂ´ng Ã„â€˜Ã¡Â»Âc Ã„â€˜Ã†Â°Ã¡Â»Â£c phÃ¡ÂºÂ£n hÃ¡Â»â€œi tÃ¡Â»Â« Ollama local.") from exc

        content = ((body.get("message") or {}).get("content") or "").strip()
        if not content:
            raise RuntimeError("Ollama trÃ¡ÂºÂ£ vÃ¡Â»Â phÃ¡ÂºÂ£n hÃ¡Â»â€œi rÃ¡Â»â€”ng.")
        return content



class AIKernelTeachingBrain:
    """Teaching Brain adapter routed through AI Kernel / Runtime Center."""

    MODE_TO_SKILL = {
        "teacher": "classroom.assistant",
        "student": "student.self_learning",
        "orchestrator": "classroom.teaching.orchestrator",
    }

    MODE_TO_PERSONA_POLICY = {
        "teacher": {
            "persona": (
                "Em là Trợ giảng Toán THCS của MathTeacher AI. "
                "Gọi người dùng là thầy/cô và xưng em. "
                "Không tự nhận mình là giáo viên."
            ),
            "policy": (
                "Ưu tiên hỗ trợ giáo viên soạn bài, giải thích Toán, "
                "thiết kế hoạt động dạy học và phản hồi sư phạm. "
                "Chỉ tư vấn; không tự ý thực hiện hành động kỹ thuật "
                "hoặc thay đổi hệ thống, dữ liệu hay bài giảng."
            ),
        },
        "student": {
            "persona": (
                "Em là Trợ lý học tập Toán THCS của MathTeacher AI. "
                "Giao tiếp trực tiếp với học sinh bằng ngôn ngữ thân thiện, dễ hiểu. "
                "Không gọi học sinh là thầy/cô, không xưng anh/chị với học sinh. "
                "Ưu tiên khuyến khích học sinh tự suy nghĩ và tự trình bày cách làm."
            ),
            "policy": (
                "Không giải ngay khi học sinh có thể tự làm. "
                "Trước hết đưa câu hỏi hoặc gợi ý nhỏ. "
                "Nếu học sinh sai, chỉ ra chỗ sai và hướng dẫn sửa. "
                "Nếu chưa hiểu, đưa ví dụ tương tự. "
                "Tăng dần mức độ hỗ trợ. "
                "Chỉ đưa lời giải đầy đủ khi thực sự phù hợp. "
                "Không thực hiện hành động thay đổi hệ thống hoặc dữ liệu."
            ),
        },
        "orchestrator": {
            "persona": (
                "Em là Trợ lý điều phối dạy học Toán THCS của MathTeacher AI. "
                "Gọi người dùng là thầy/cô và xưng em."
            ),
            "policy": (
                "Tập trung đề xuất cách tổ chức hoạt động, tiến trình và "
                "phối hợp các thành phần hỗ trợ dạy học. "
                "Chỉ tư vấn và đề xuất. "
                "Mọi hành động thực tế trong lớp học phải được chuyển qua "
                "Classroom Controller/Approval layer theo quyền được cấp."
            ),
        },
    }

    def __init__(self, service=None):
        from ai_kernel.service import AIKernelService
        self.service = service or AIKernelService()

    def respond(self, *, transcript, system_prompt, history=(), mode="teacher"):
        normalized_mode = str(mode or "teacher").strip().lower()
        skill_id = self.MODE_TO_SKILL.get(
            normalized_mode,
            self.MODE_TO_SKILL["teacher"],
        )

        from ai_kernel.contracts import AIOwnership, AIActionClass

        history_lines = []
        for item in history[-8:]:
            role = item.get("role", "unknown")
            content = item.get("content", "")
            history_lines.append(f"{role}: {content}")

        history_text = "\n".join(history_lines) if history_lines else "(no history)"

        persona_policy = self.MODE_TO_PERSONA_POLICY.get(
            normalized_mode,
            self.MODE_TO_PERSONA_POLICY["teacher"],
        )

        prompt = (
            system_prompt
            + "\n\nPersona:\n"
            + persona_policy["persona"]
            + "\n\nPolicy:\n"
            + persona_policy["policy"]
            + "\n\nRecent conversation:\n"
            + history_text
            + "\n\nUser says:\n"
            + transcript
            + "\n\nRespond directly in Vietnamese according to the selected Persona and Policy."
        )

        response = self.service.run(
            task_id="teaching_assistant_voice",
            prompt=prompt,
            capabilities=("general", "vietnamese", "mathematics"),
            owner=AIOwnership.USER,
            action=AIActionClass.ADVISORY,
            metadata={
                "channel": "voice",
                "interface": "teaching_assistant",
                "mutating": "false",
            },
            skill_id=skill_id,
        )
        return response.text


class FasterWhisperSTT:
    """Optional local STT adapter using faster-whisper.

    The dependency is imported lazily so MathTeacher AI can run without STT installed.
    """

    def __init__(self, model_size: str = "tiny", *, device: str = "auto", compute_type: str = "int8") -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _ensure_model(self) -> Any:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "ChÃ†Â°a cÃƒÂ i faster-whisper. HÃƒÂ£y cÃƒÂ i adapter STT local trÃ†Â°Ã¡Â»â€ºc khi dÃƒÂ¹ng microphone/audio."
                ) from exc
            device = "cpu" if self.device == "auto" else self.device
            self._model = WhisperModel(self.model_size, device=device, compute_type=self.compute_type)
        return self._model

    def transcribe(self, audio_path: str | Path, *, language: str = "vi") -> STTResult:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(path)
        model = self._ensure_model()
        segments, info = model.transcribe(str(path), language=language, vad_filter=True)
        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
        confidence = None
        avg_logprob = getattr(info, "language_probability", None)
        if isinstance(avg_logprob, (int, float)):
            confidence = float(avg_logprob)
        return STTResult(
            text=text,
            language=getattr(info, "language", language) or language,
            confidence=confidence,
            provider="faster-whisper",
            metadata={"model_size": self.model_size, "device": self.device, "compute_type": self.compute_type},
        )


class CommandTTSAdapter:
    """Replaceable local TTS adapter.

    command_template can contain `{text}` and `{output}` placeholders.
    The command is parsed before inserting dynamic text, then executed
    without shell=True so Vietnamese text and punctuation are passed
    safely as a single argument on Windows.
    """

    def __init__(self, command_template: str) -> None:
        if "{text}" not in command_template or "{output}" not in command_template:
            raise ValueError("command_template phÃ¡ÂºÂ£i cÃƒÂ³ {text} vÃƒÂ  {output}.")

        self.command_template = command_template

        try:
            self._command_parts = shlex.split(command_template, posix=False)
        except ValueError as exc:
            raise ValueError(
                f"command_template khÃƒÂ´ng hÃ¡Â»Â£p lÃ¡Â»â€¡: {exc}"
            ) from exc

        if not self._command_parts:
            raise ValueError("command_template khÃƒÂ´ng Ã„â€˜Ã†Â°Ã¡Â»Â£c rÃ¡Â»â€”ng.")

    @staticmethod
    def _strip_outer_quotes(value: str) -> str:
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            return value[1:-1]
        return value

    def synthesize(self, text: str, *, output_path: str | Path) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        args: list[str] = []

        for part in self._command_parts:
            part = part.replace("{text}", text)
            part = part.replace("{output}", str(output))
            part = self._strip_outer_quotes(part)
            args.append(part)

        completed = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if completed.returncode != 0:
            raise RuntimeError(
                (completed.stderr or completed.stdout or "TTS command failed").strip()
            )

        if not output.exists():
            raise RuntimeError(
                "TTS command chÃ¡ÂºÂ¡y xong nhÃ†Â°ng khÃƒÂ´ng tÃ¡ÂºÂ¡o output."
            )

        return output


@dataclass(frozen=True)
class TeachingVoiceTurn:
    transcript: STTResult
    response_text: str
    synthesized_audio: Path | None = None


class TeachingAssistantVoiceBridge:
    """STT -> local brain -> optional TTS bridge.

    Classroom actions are intentionally not executed here. The returned text can be
    passed through the existing TeachingAssistantController/Agent/Approval layers.
    """

    def __init__(
        self,
        *,
        stt: SpeechToTextProvider,
        brain: TeachingBrain,
        tts: TextToSpeechProvider | None = None,
        config: TeachingVoiceConfig | None = None,
    ) -> None:
        self.stt = stt
        self.brain = brain
        self.tts = tts
        self.config = config or TeachingVoiceConfig()
        self.mode = self.config.mode
        self.history: list[Mapping[str, str]] = []

    def process_audio(self, audio_path: str | Path, *, output_path: str | Path | None = None) -> TeachingVoiceTurn:
        transcript = self.stt.transcribe(audio_path, language="vi")
        if not transcript.text:
            raise RuntimeError("Khong nhan dien duoc noi dung am thanh.")

        response = self.brain.respond(
            transcript=transcript.text,
            system_prompt=self.config.system_prompt,
            history=tuple(self.history[-8:]),
            mode=self.mode,
        )

        self.history.extend((
            {"role": "user", "content": transcript.text},
            {"role": "assistant", "content": response},
        ))

        audio = None
        if self.tts is not None:
            if output_path is None:
                raise RuntimeError("Neu bat TTS thi phai cung cap output_path.")
            audio = self.tts.synthesize(response, output_path=output_path)

        return TeachingVoiceTurn(
            transcript=transcript,
            response_text=response,
            synthesized_audio=audio,
        )

__all__ = [
    "CommandTTSAdapter",
    "FasterWhisperSTT",
    "OllamaTeachingBrain",
    "STTResult",
    "SpeechToTextProvider",
    "TeachingAssistantVoiceBridge",
    "TeachingBrain",
    "TeachingVoiceConfig",
    "TeachingVoiceTurn",
    "TextToSpeechProvider",
]
