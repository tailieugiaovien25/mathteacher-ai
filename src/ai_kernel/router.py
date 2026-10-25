from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ai_platform.contracts import AIProvider, AIRequest
from ai_platform.providers.ollama import OllamaProvider

from .audit import make_audit_event
from .contracts import AIKernelRequest, AIKernelResponse
from .governance import AIKernelGovernance
from .profiles import ModelCapability, ModelProfile, default_model_profiles
from .runtime_registry import AIRuntimeManager
from .skills import AISkillSpec, default_ai_skills


@dataclass(frozen=True)
class RouteDecision:
    profile: ModelProfile


class AIRouter:
    """Route tasks to an ADMIN-approved local model profile."""

    def __init__(
        self,
        provider: AIProvider | None,
        *,
        profiles: tuple[ModelProfile, ...] | None = None,
        skills: tuple[AISkillSpec, ...] | None = None,
        governance: AIKernelGovernance | None = None,
        provider_factory: Callable[[ModelProfile], AIProvider] | None = None,
        runtime_manager: AIRuntimeManager | None = None,
    ) -> None:
        self.provider = provider
        self.profiles = profiles or default_model_profiles()
        self.skills = skills or default_ai_skills()
        self.governance = governance or AIKernelGovernance()
        self.provider_factory = provider_factory
        self.runtime_manager = runtime_manager

    def _resolve_skill(self, request: AIKernelRequest) -> AISkillSpec | None:
        if not request.skill_id:
            return None
        for skill in self.skills:
            if skill.skill_id == request.skill_id:
                if not skill.admin_enabled:
                    raise RuntimeError(f"AI skill chÆ°a Ä‘Æ°á»£c ADMIN báº­t: {request.skill_id}")
                if request.action not in skill.allowed_actions and request.owner.value != "admin":
                    raise RuntimeError(f"AI skill khÃ´ng cho phÃ©p action {request.action.value}: {request.skill_id}")
                return skill
        raise RuntimeError(f"KhÃ´ng tÃ¬m tháº¥y AI skill: {request.skill_id}")

    def choose(self, request: AIKernelRequest) -> RouteDecision:
        self.governance.authorize_request(request)
        self._resolve_skill(request)
        requested = {
            ModelCapability(item)
            for item in request.requested_capabilities
            if item in {cap.value for cap in ModelCapability}
        }
        if self.runtime_manager is not None:
            enabled = self.runtime_manager.enabled_profiles()
            active = self.runtime_manager.active_profile()
        else:
            enabled = tuple(profile for profile in self.profiles if profile.admin_enabled)
            active = enabled[0] if enabled else None
        if not enabled:
            raise RuntimeError("KhÃ´ng cÃ³ model profile nÃ o Ä‘Æ°á»£c ADMIN báº­t.")
        if active is None:
            raise RuntimeError("KhÃ´ng xÃ¡c Ä‘á»‹nh Ä‘Æ°á»£c active AI profile.")

        if requested and not requested.issubset(active.capabilities):
            ranked = sorted(
                enabled,
                key=lambda profile: len(requested.intersection(profile.capabilities)),
                reverse=True,
            )
            if not ranked or len(requested.intersection(ranked[0].capabilities)) == 0:
                raise RuntimeError(
                    f"Active profile {active.profile_id} khÃ´ng Ä‘Ã¡p á»©ng capability yÃªu cáº§u."
                )

        return RouteDecision(active)

    def _provider_for(self, profile: ModelProfile) -> AIProvider:
        if self.provider_factory is not None:
            return self.provider_factory(profile)
        if self.provider is not None and getattr(self.provider, "provider_id", "") == profile.provider:
            current_model = str(getattr(self.provider, "model", "") or "")
            if current_model == profile.model:
                return self.provider
            if profile.provider == "ollama":
                base_url = str(getattr(self.provider, "base_url", "http://127.0.0.1:11434"))
                return OllamaProvider(base_url=base_url, model=profile.model)
        if profile.provider == "ollama":
            return OllamaProvider(model=profile.model)
        if self.provider is None:
            raise RuntimeError(f"ChÆ°a cÃ³ provider cho profile {profile.profile_id}.")
        return self.provider

    def stream(self, request: AIKernelRequest):
        decision = self.choose(request)
        event = make_audit_event(request, decision.profile.profile_id)
        provider = self._provider_for(decision.profile)

        stream_method = getattr(provider, "stream", None)
        if not callable(stream_method):
            raise RuntimeError(
                f"Provider {decision.profile.provider} không hỗ trợ streaming."
            )

        ai_request = AIRequest(
            task=request.task_id,
            prompt=request.prompt,
            system_prompt=(
                "MathTeacher AI Kernel. Tuân thủ governance: "
                "không tự sửa code lõi, không tự đổi policy, "
                "không tự thực hiện thao tác production. "
                "Chỉ đưa ra kết luận dựa trên bằng chứng đã cung cấp."
            ),
            metadata={
                **dict(request.metadata),
                "profile_id": decision.profile.profile_id,
                "ownership": request.owner.value,
                "action": request.action.value,
                "audit_id": event.audit_id,
            },
        )
        return stream_method(ai_request)
    def generate(self, request: AIKernelRequest) -> AIKernelResponse:
        decision = self.choose(request)
        event = make_audit_event(request, decision.profile.profile_id)
        provider = self._provider_for(decision.profile)
        ai_response = provider.generate(
            AIRequest(
                task=request.task_id,
                prompt=request.prompt,
                system_prompt=(
                    "MathTeacher AI Kernel. TuÃ¢n thá»§ governance: "
                    "khÃ´ng tá»± sá»­a code lÃµi, khÃ´ng tá»± Ä‘á»•i policy, "
                    "khÃ´ng tá»± thá»±c hiá»‡n thao tÃ¡c production. "
                    "Chá»‰ Ä‘Æ°a ra káº¿t luáº­n dá»±a trÃªn báº±ng chá»©ng Ä‘Ã£ cung cáº¥p."
                ),
                metadata={
                    **dict(request.metadata),
                    "profile_id": decision.profile.profile_id,
                    "ownership": request.owner.value,
                    "action": request.action.value,
                },
            )
        )
        return AIKernelResponse(
            text=ai_response.text,
            provider=ai_response.provider,
            model=ai_response.model,
            profile_id=decision.profile.profile_id,
            task_id=request.task_id,
            audit_id=event.audit_id,
            action=request.action,
            used_fallback=ai_response.used_fallback,
        )
