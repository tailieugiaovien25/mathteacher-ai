from __future__ import annotations

from .config import AIPlatformConfig
from .contracts import AIProvider
from .providers.ollama import OllamaProvider


def build_ai_provider(config: AIPlatformConfig | None = None) -> AIProvider | None:
    resolved = config or AIPlatformConfig.from_environment()
    if resolved.provider == "ollama":
        return OllamaProvider(base_url=resolved.ollama_base_url, model=resolved.model)
    return None
