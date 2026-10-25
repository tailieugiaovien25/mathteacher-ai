from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Mapping


@dataclass(frozen=True)
class LiveKitTransportConfig:
    """Optional self-hosted LiveKit transport configuration.

    This layer deliberately does not import the LiveKit SDK. MathTeacher AI keeps
    the media transport replaceable and can run without LiveKit installed.
    """

    url: str = "ws://127.0.0.1:7880"
    room_name: str = "mathteacher-ai-teaching-assistant"
    identity_prefix: str = "mathteacher-ta"
    api_key_env: str = "LIVEKIT_API_KEY"
    api_secret_env: str = "LIVEKIT_API_SECRET"
    token_ttl_seconds: int = 3600
    publish_audio: bool = True
    publish_video: bool = True
    subscribe_audio: bool = True
    subscribe_video: bool = True
    metadata: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "LiveKitTransportConfig":
        return cls(
            url=os.environ.get("MATHTEACHER_LIVEKIT_URL", "ws://127.0.0.1:7880"),
            room_name=os.environ.get(
                "MATHTEACHER_LIVEKIT_ROOM",
                "mathteacher-ai-teaching-assistant",
            ),
            identity_prefix=os.environ.get("MATHTEACHER_LIVEKIT_IDENTITY_PREFIX", "mathteacher-ta"),
            api_key_env=os.environ.get("MATHTEACHER_LIVEKIT_API_KEY_ENV", "LIVEKIT_API_KEY"),
            api_secret_env=os.environ.get("MATHTEACHER_LIVEKIT_API_SECRET_ENV", "LIVEKIT_API_SECRET"),
            token_ttl_seconds=max(
                60,
                int(os.environ.get("MATHTEACHER_LIVEKIT_TOKEN_TTL", "3600")),
            ),
        )


@dataclass(frozen=True)
class LiveKitRoomDescriptor:
    url: str
    room_name: str
    identity: str
    can_publish_audio: bool = True
    can_publish_video: bool = True
    can_subscribe_audio: bool = True
    can_subscribe_video: bool = True


def build_livekit_room_descriptor(
    config: LiveKitTransportConfig,
    *,
    identity_suffix: str | None = None,
) -> LiveKitRoomDescriptor:
    suffix = identity_suffix or "teacher"
    identity = f"{config.identity_prefix}-{suffix}".strip("-")
    return LiveKitRoomDescriptor(
        url=config.url,
        room_name=config.room_name,
        identity=identity,
        can_publish_audio=config.publish_audio,
        can_publish_video=config.publish_video,
        can_subscribe_audio=config.subscribe_audio,
        can_subscribe_video=config.subscribe_video,
    )


def livekit_environment_status(config: LiveKitTransportConfig) -> dict[str, object]:
    api_key_present = bool(os.environ.get(config.api_key_env, "").strip())
    api_secret_present = bool(os.environ.get(config.api_secret_env, "").strip())
    return {
        "transport": "livekit",
        "self_hosted": config.url.startswith(("ws://127.0.0.1", "ws://localhost", "wss://127.0.0.1", "wss://localhost")),
        "url": config.url,
        "room_name": config.room_name,
        "api_key_present": api_key_present,
        "api_secret_present": api_secret_present,
        "sdk_installed": _livekit_sdk_available(),
    }


def _livekit_sdk_available() -> bool:
    try:
        import livekit  # type: ignore  # pragma: no cover - optional dependency
    except ImportError:
        return False
    return livekit is not None


__all__ = [
    "LiveKitRoomDescriptor",
    "LiveKitTransportConfig",
    "build_livekit_room_descriptor",
    "livekit_environment_status",
]

# Optional token helper kept here for compatibility with existing transport imports.
from .teaching_livekit import LiveKitParticipantToken, generate_livekit_access_token  # noqa: E402,F401
