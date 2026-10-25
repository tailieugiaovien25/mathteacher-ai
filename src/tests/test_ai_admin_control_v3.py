from __future__ import annotations

from ai_kernel import AIAdminControl, ModelCapability, ModelProfile


def test_admin_control_resolves_exact_enabled_profile():
    profiles = (
        ModelProfile(
            profile_id="local-a",
            provider="ollama",
            model="qwen3:8b",
            capabilities=frozenset({ModelCapability.GENERAL}),
            admin_enabled=True,
        ),
        ModelProfile(
            profile_id="local-b",
            provider="ollama",
            model="qwen3:30b",
            capabilities=frozenset({ModelCapability.REASONING}),
            admin_enabled=False,
        ),
    )
    control = AIAdminControl(profiles)
    snapshot = control.snapshot(provider="ollama", model="qwen3:8b")
    assert snapshot.active_profile_id == "local-a"
    assert snapshot.enabled_profile_ids == ("local-a",)


def test_admin_control_does_not_silently_enable_disabled_model():
    profiles = (
        ModelProfile(
            profile_id="local-a",
            provider="ollama",
            model="qwen3:8b",
            capabilities=frozenset({ModelCapability.GENERAL}),
            admin_enabled=True,
        ),
        ModelProfile(
            profile_id="local-b",
            provider="ollama",
            model="qwen3:30b",
            capabilities=frozenset({ModelCapability.REASONING}),
            admin_enabled=False,
        ),
    )
    snapshot = AIAdminControl(profiles).snapshot(provider="ollama", model="qwen3:30b")
    assert snapshot.active_profile_id == "local-a"
    assert "local-b" not in snapshot.enabled_profile_ids
