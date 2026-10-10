from __future__ import annotations

from ai_platform.providers.ollama import OllamaProvider


def test_ollama_provider_exposes_local_health_and_model_methods():
    provider = OllamaProvider()
    assert callable(provider.health)
    assert callable(provider.list_models)
