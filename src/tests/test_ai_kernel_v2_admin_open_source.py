from __future__ import annotations

import pytest

from ai_kernel import (
    AIActionClass,
    AIKernelGovernance,
    AIKernelRequest,
    AdminPolicyError,
    AIOwnership,
    default_model_profiles,
)


def test_kernel_default_profiles_are_admin_enabled_and_ollama_backed():
    profiles = default_model_profiles()
    assert profiles
    assert all(item.admin_enabled for item in profiles)
    assert all(item.provider == "ollama" for item in profiles)


def test_kernel_blocks_user_mutation():
    governance = AIKernelGovernance()
    request = AIKernelRequest(
        task_id="t",
        prompt="do something",
        owner=AIOwnership.USER,
        action=AIActionClass.MUTATING,
    )
    with pytest.raises(AdminPolicyError):
        governance.authorize_request(request)


def test_kernel_allows_admin_configuration_request():
    governance = AIKernelGovernance()
    request = AIKernelRequest(
        task_id="t",
        prompt="review config",
        owner=AIOwnership.ADMIN,
        action=AIActionClass.GOVERNANCE,
    )
    governance.authorize_request(request)


def test_kernel_blocks_self_modification():
    governance = AIKernelGovernance()
    with pytest.raises(AdminPolicyError):
        governance.authorize_self_modification()


def test_router_uses_only_admin_selected_profile():
    from ai_kernel.router import AIRouter
    from ai_kernel.profiles import ModelCapability, ModelProfile
    from ai_platform.contracts import AIResponse

    class FakeProvider:
        provider_id = "ollama"
        model = "admin-model"

        def generate(self, request):
            return AIResponse(
                text="ok",
                provider=self.provider_id,
                model=self.model,
            )

    profile = ModelProfile(
        profile_id="admin-selected",
        provider="ollama",
        model="admin-model",
        capabilities=frozenset({ModelCapability.DOCUMENT}),
    )
    router = AIRouter(FakeProvider(), profiles=(profile,))
    response = router.generate(
        AIKernelRequest(
            task_id="doc-audit",
            prompt="review",
            owner=AIOwnership.SYSTEM,
            requested_capabilities=("document",),
            action=AIActionClass.ADVISORY,
        )
    )
    assert response.profile_id == "admin-selected"
    assert response.model == "admin-model"
    assert response.audit_id.startswith("aik_")
