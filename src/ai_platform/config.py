from __future__ import annotations

from dataclasses import dataclass, field
import os


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AIPlatformConfig:
    """Central runtime switches. Secrets are never stored here."""

    provider: str = "ollama"
    model: str = "qwen3:8b"
    system_admin_enabled: bool = False
    marketing_enabled: bool = False
    commercial_mode: bool = False
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_api_key: str = field(default="", repr=False, compare=False)
    runtime_config_authoritative: bool = field(default=False, repr=False, compare=False)

    @classmethod
    def from_environment(cls) -> "AIPlatformConfig":
        return cls(
            provider=os.getenv("MATH_TEACHER_AI_PROVIDER", "ollama").strip().casefold() or "ollama",
            model=os.getenv("MATH_TEACHER_AI_MODEL", "qwen3:8b").strip() or "qwen3:8b",
            system_admin_enabled=_env_bool("SYSTEM_ADMIN_AI_ENABLED", False),
            marketing_enabled=_env_bool("MARKETING_AI_ENABLED", False),
            commercial_mode=_env_bool("MATH_TEACHER_COMMERCIAL_MODE", False),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/") or "http://127.0.0.1:11434",
            ollama_api_key=os.getenv("OLLAMA_API_KEY", "").strip(),
            runtime_config_authoritative=any(
                os.getenv(name, "").strip()
                for name in (
                    "MATH_TEACHER_AI_PROVIDER",
                    "MATH_TEACHER_AI_MODEL",
                    "OLLAMA_BASE_URL",
                )
            ),
        )

    @property
    def marketing_runtime_enabled(self) -> bool:
        return self.commercial_mode and self.marketing_enabled
