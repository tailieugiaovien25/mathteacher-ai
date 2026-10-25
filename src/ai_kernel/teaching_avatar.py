from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import shlex
import subprocess
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


class AvatarState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    STOPPED = "stopped"


@dataclass(frozen=True)
class AvatarProfile:
    avatar_id: str
    display_name: str
    image_path: str | Path
    renderer_id: str = "static"
    lip_sync_id: str = "none"
    language: str = "vi-VN"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AvatarFrame:
    avatar_id: str
    state: AvatarState
    media_path: Path | None = None
    audio_path: Path | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class AvatarRenderer(Protocol):
    renderer_id: str

    def render(
        self,
        *,
        profile: AvatarProfile,
        state: AvatarState,
        audio_path: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> AvatarFrame: ...


class LipSyncProvider(Protocol):
    provider_id: str

    def synthesize(
        self,
        *,
        avatar_image: str | Path,
        audio_path: str | Path,
        output_path: str | Path,
    ) -> Path: ...


class StaticAvatarRenderer:
    """Dependency-free renderer for UI experiments.

    It exposes avatar state without generating video. A future WebRTC/WebSocket
    renderer can subscribe to the same AvatarFrame contract.
    """

    renderer_id = "static"

    def render(
        self,
        *,
        profile: AvatarProfile,
        state: AvatarState,
        audio_path: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> AvatarFrame:
        del output_path
        media = Path(profile.image_path)
        if not media.exists():
            raise FileNotFoundError(media)
        return AvatarFrame(
            avatar_id=profile.avatar_id,
            state=state,
            media_path=media,
            audio_path=Path(audio_path) if audio_path else None,
            metadata={"renderer_id": self.renderer_id},
        )


class CommandLipSyncProvider:
    """Replaceable local lip-sync adapter.

    The command is executed without a shell and supports these placeholders:
    `{avatar}`, `{audio}`, `{output}`. The concrete engine can be MuseTalk,
    LivePortrait-based tooling, or another local/open model.
    """

    def __init__(self, command_template: Sequence[str], *, provider_id: str = "command") -> None:
        if not command_template:
            raise ValueError("command_template không được rỗng.")
        self.command_template = tuple(command_template)
        self.provider_id = provider_id
        required = {"{avatar}", "{audio}", "{output}"}
        if not required.issubset(set(command_template)):
            raise ValueError("command_template phải chứa {avatar}, {audio}, {output}.")

    @classmethod
    def from_shell_like_template(cls, template: str, *, provider_id: str = "command") -> "CommandLipSyncProvider":
        return cls(shlex.split(template), provider_id=provider_id)

    def synthesize(
        self,
        *,
        avatar_image: str | Path,
        audio_path: str | Path,
        output_path: str | Path,
    ) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        values = {
            "{avatar}": str(Path(avatar_image)),
            "{audio}": str(Path(audio_path)),
            "{output}": str(output),
        }
        command = [item.replace("{avatar}", values["{avatar}"]).replace("{audio}", values["{audio}"]).replace("{output}", values["{output}"]) for item in self.command_template]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "Lip-sync command failed").strip())
        if not output.exists():
            raise RuntimeError("Lip-sync command chạy xong nhưng không tạo output.")
        return output


class TeachingAvatarSession:
    """Maps voice-session states to a replaceable avatar/lip-sync pipeline.

    This class is deliberately presentation-only. It cannot execute classroom
    tools or modify lessons.
    """

    def __init__(
        self,
        *,
        profile: AvatarProfile,
        renderer: AvatarRenderer,
        lip_sync: LipSyncProvider | None = None,
    ) -> None:
        self.profile = profile
        self.renderer = renderer
        self.lip_sync = lip_sync
        self.frames: list[AvatarFrame] = []

    def set_state(self, state: AvatarState) -> AvatarFrame:
        frame = self.renderer.render(profile=self.profile, state=state)
        self.frames.append(frame)
        return frame

    def speak(
        self,
        *,
        audio_path: str | Path,
        output_path: str | Path | None = None,
    ) -> AvatarFrame:
        audio = Path(audio_path)
        if not audio.exists():
            raise FileNotFoundError(audio)
        if self.lip_sync is None:
            frame = self.renderer.render(
                profile=self.profile,
                state=AvatarState.SPEAKING,
                audio_path=audio,
            )
        else:
            if output_path is None:
                raise ValueError("Đã cấu hình lip-sync thì phải cung cấp output_path.")
            media = self.lip_sync.synthesize(
                avatar_image=self.profile.image_path,
                audio_path=audio,
                output_path=output_path,
            )
            frame = AvatarFrame(
                avatar_id=self.profile.avatar_id,
                state=AvatarState.SPEAKING,
                media_path=media,
                audio_path=audio,
                metadata={
                    "renderer_id": self.renderer.renderer_id,
                    "lip_sync_id": self.lip_sync.provider_id,
                },
            )
        self.frames.append(frame)
        return frame


def default_avatar_profiles() -> tuple[AvatarProfile, ...]:
    return (
        AvatarProfile(
            avatar_id="math_assistant_female_vi",
            display_name="Trợ giảng Toán",
            image_path="assets/avatars/math_assistant_female_vi.svg",
            renderer_id="static",
            lip_sync_id="none",
            language="vi-VN",
        ),
    )


__all__ = [
    "AvatarFrame",
    "AvatarProfile",
    "AvatarRenderer",
    "AvatarState",
    "CommandLipSyncProvider",
    "LipSyncProvider",
    "StaticAvatarRenderer",
    "TeachingAvatarSession",
    "default_avatar_profiles",
]
