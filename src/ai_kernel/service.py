from __future__ import annotations

from dataclasses import dataclass

from ai_platform.config import AIPlatformConfig
from ai_platform.factory import build_ai_provider

from .contracts import AIActionClass, AIOwnership, AIKernelRequest, AIKernelResponse
from .governance import AIKernelGovernance
from .router import AIRouter
from .profiles import ModelProfile, default_model_profiles
from .runtime_registry import AIRuntimeManager
from .skills import AISkillSpec


@dataclass(frozen=True)
class AIKernelHealth:
    enabled: bool
    provider: str
    configured_model: str
    governance_admin_owned: bool = True


class AIKernelService:
    """Single entry point for AI capabilities; governance stays ADMIN-owned."""

    def __init__(self, *, config: AIPlatformConfig | None = None, governance: AIKernelGovernance | None = None, profiles: tuple[ModelProfile, ...] | None = None, skills: tuple[AISkillSpec, ...] | None = None):
        self.config = config or AIPlatformConfig.from_environment()
        self.governance = governance or AIKernelGovernance()
        resolved_profiles = profiles or default_model_profiles()
        self.runtime_manager = AIRuntimeManager(
            profiles=resolved_profiles,
            governance=self.governance,
            provider=self.config.provider,
            base_url=self.config.ollama_base_url,
            selected_profile_id=next((p.profile_id for p in resolved_profiles if p.provider == self.config.provider and p.model == self.config.model), ""),
        )
        provider = build_ai_provider(self.config)
        self.router = AIRouter(
            provider,
            governance=self.governance,
            profiles=resolved_profiles,
            skills=skills,
            runtime_manager=self.runtime_manager,
        )

    def health(self) -> AIKernelHealth:
        active = self.runtime_manager.active_profile()
        return AIKernelHealth(
            enabled=self.router.provider is not None,
            provider=active.provider,
            configured_model=active.model,
        )

    def stream(
        self,
        *,
        task_id: str,
        prompt: str,
        capabilities: tuple[str, ...] = (),
        owner: AIOwnership = AIOwnership.USER,
        action: AIActionClass = AIActionClass.ADVISORY,
        metadata: dict[str, str] | None = None,
        skill_id: str = "",
    ):
        request = AIKernelRequest(
            task_id=task_id,
            prompt=prompt,
            owner=owner,
            action=action,
            requested_capabilities=capabilities,
            metadata=metadata or {},
            skill_id=skill_id,
        )
        return self.router.stream(request)
    def run(
        self,
        *,
        task_id: str,
        prompt: str,
        capabilities: tuple[str, ...] = (),
        owner: AIOwnership = AIOwnership.USER,
        action: AIActionClass = AIActionClass.ADVISORY,
        metadata: dict[str, str] | None = None,
        skill_id: str = "",
    ) -> AIKernelResponse:
        request = AIKernelRequest(
            task_id=task_id,
            prompt=prompt,
            owner=owner,
            action=action,
            requested_capabilities=capabilities,
            metadata=metadata or {},
            skill_id=skill_id,
        )
        return self.router.generate(request)
