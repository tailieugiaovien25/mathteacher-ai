from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from ai_platform.contracts import AIProvider, AIRequest
from ai_platform.providers.ollama import OllamaProvider, OllamaProviderError

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
                api_key = str(getattr(self.provider, "api_key", "") or "")
                return OllamaProvider(base_url=base_url, model=profile.model, api_key=api_key)
        if profile.provider == "ollama":
            return OllamaProvider(model=profile.model)
        if self.provider is None:
            raise RuntimeError(f"ChÆ°a cÃ³ provider cho profile {profile.profile_id}.")
        return self.provider

    def _try_local_agent_fallback(
        self,
        request: AIKernelRequest,
        ai_request: AIRequest,
        primary_error: OllamaProviderError,
    ) -> tuple[ModelProfile, object] | None:
        enabled = os.getenv("MATH_TEACHER_AI_LOCAL_FALLBACK_ENABLED", "").strip().casefold()
        if (
            primary_error.status_code != 402
            or enabled not in {"1", "true", "yes", "on"}
            or request.metadata.get("interface") != "chief_engineer_agent"
            or self.runtime_manager is None
        ):
            return None

        fallback_profile = next(
            (
                profile
                for profile in self.runtime_manager.fallback_profiles()
                if profile.profile_id == "qwen3-local-0.6b"
                and profile.provider == "ollama"
            ),
            None,
        )
        if fallback_profile is None:
            raise OllamaProviderError(
                "Ollama Cloud hết credit; Qwen 3 0.6B chưa được ADMIN bật làm fallback."
            ) from primary_error

        local_url = (
            os.getenv("MATH_TEACHER_AI_LOCAL_OLLAMA_URL", "http://127.0.0.1:11434")
            .strip()
            .rstrip("/")
        )
        local_provider = OllamaProvider(
            base_url=local_url,
            model=fallback_profile.model,
        )
        if not local_provider.health():
            raise OllamaProviderError(
                "Ollama Cloud hết credit nhưng không kết nối được Ollama local tại "
                f"{local_url}. Bản chạy Streamlit Cloud không thể truy cập Ollama trên PC cá nhân."
            ) from primary_error
        if fallback_profile.model not in local_provider.list_models():
            raise OllamaProviderError(
                "Ollama Cloud hết credit nhưng máy local chưa có model qwen3:0.6b; "
                "hãy chạy `ollama pull qwen3:0.6b`."
            ) from primary_error

        fallback_request = AIRequest(
            task=ai_request.task,
            prompt=ai_request.prompt,
            system_prompt=ai_request.system_prompt,
            metadata={
                **dict(ai_request.metadata),
                "profile_id": fallback_profile.profile_id,
                "ollama_num_ctx": str(fallback_profile.context_window),
                "provider_fallback_from": "ollama-cloud-http-402",
            },
        )
        try:
            return fallback_profile, local_provider.generate(fallback_request)
        except OllamaProviderError as fallback_error:
            raise OllamaProviderError(
                "Ollama Cloud hết credit và Qwen 3 0.6B local cũng thất bại: "
                f"{fallback_error}"
            ) from primary_error

    def stream(self, request: AIKernelRequest):
        decision = self.choose(request)
        event = make_audit_event(request, decision.profile.profile_id)
        provider = self._provider_for(decision.profile)

        stream_method = getattr(provider, "stream", None)
        if not callable(stream_method):
            raise RuntimeError(
                f"Provider {decision.profile.provider} không hỗ trợ streaming."
            )

        provider_metadata = {
            **dict(request.metadata),
            "profile_id": decision.profile.profile_id,
            "ownership": request.owner.value,
            "action": request.action.value,
            "audit_id": event.audit_id,
        }
        if decision.profile.provider == "ollama":
            provider_metadata["ollama_num_ctx"] = str(decision.profile.context_window)

        ai_request = AIRequest(
            task=request.task_id,
            prompt=request.prompt,
            system_prompt=(
                "MathTeacher AI Kernel. Tuân thủ governance: "
                "không tự sửa code lõi, không tự đổi policy, "
                "không tự thực hiện thao tác production. "
                "Chỉ đưa ra kết luận dựa trên bằng chứng đã cung cấp."
            ),
            metadata=provider_metadata,
        )
        return stream_method(ai_request)
    def generate(self, request: AIKernelRequest) -> AIKernelResponse:
        decision = self.choose(request)
        event = make_audit_event(request, decision.profile.profile_id)
        provider = self._provider_for(decision.profile)
        provider_metadata = {
            **dict(request.metadata),
            "profile_id": decision.profile.profile_id,
            "ownership": request.owner.value,
            "action": request.action.value,
        }
        if decision.profile.provider == "ollama":
            provider_metadata["ollama_num_ctx"] = str(decision.profile.context_window)

        ai_request = AIRequest(
            task=request.task_id,
            prompt=request.prompt,
            system_prompt=(
                "MathTeacher AI Kernel. Tuân thủ governance: "
                "không tự sửa code lõi, không tự đổi policy, "
                "không tự thực hiện thao tác production. "
                "Chỉ đưa ra kết luận dựa trên bằng chứng đã cung cấp."
            ),
            metadata=provider_metadata,
        )
        response_profile = decision.profile
        try:
            ai_response = provider.generate(ai_request)
        except OllamaProviderError as exc:
            fallback = self._try_local_agent_fallback(request, ai_request, exc)
            if fallback is None:
                raise
            response_profile, ai_response = fallback
        return AIKernelResponse(
            text=ai_response.text,
            provider=ai_response.provider,
            model=ai_response.model,
            profile_id=response_profile.profile_id,
            task_id=request.task_id,
            audit_id=event.audit_id,
            action=request.action,
            used_fallback=ai_response.used_fallback or response_profile != decision.profile,
        )
