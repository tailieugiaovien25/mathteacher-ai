from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .profiles import ModelProfile, default_model_profiles
from .skills import AISkillSpec, default_ai_skills


@dataclass(frozen=True)
class AdminModelSnapshot:
    """ADMIN-owned, read-only snapshot of the AI model registry."""

    active_profile_id: str
    provider: str
    model: str
    enabled_profile_ids: tuple[str, ...]


class AIAdminControl:
    """Central, side-effect-free view of ADMIN AI configuration.

    This object never persists or mutates configuration. Persistence belongs to
    the ADMIN configuration layer, keeping the Kernel invariant while model
    data/configuration can change.
    """

    def __init__(self, profiles: Iterable[ModelProfile] | None = None, skills: Iterable[AISkillSpec] | None = None) -> None:
        self._profiles = tuple(profiles or default_model_profiles())
        self._skills = tuple(skills or default_ai_skills())

    @property
    def profiles(self) -> tuple[ModelProfile, ...]:
        return self._profiles

    @property
    def skills(self) -> tuple[AISkillSpec, ...]:
        return self._skills

    def enabled_skills(self) -> tuple[AISkillSpec, ...]:
        return tuple(item for item in self._skills if item.admin_enabled)

    def resolve_skill(self, skill_id: str) -> AISkillSpec:
        normalized = str(skill_id or "").strip()
        for item in self.enabled_skills():
            if item.skill_id == normalized:
                return item
        raise RuntimeError(f"ADMIN chưa bật AI skill: {normalized}")

    def enabled_profiles(self) -> tuple[ModelProfile, ...]:
        return tuple(item for item in self._profiles if item.admin_enabled)

    def resolve_active(self, *, provider: str, model: str) -> ModelProfile:
        provider_norm = str(provider or "").strip().casefold()
        model_norm = str(model or "").strip()
        for profile in self.enabled_profiles():
            if profile.provider.casefold() == provider_norm and profile.model == model_norm:
                return profile
        # Do not silently elevate to a different model. The first enabled profile
        # is only a fallback snapshot when ADMIN has not selected a known profile.
        enabled = self.enabled_profiles()
        if not enabled:
            raise RuntimeError("ADMIN chưa bật model profile nào.")
        return enabled[0]

    def snapshot(self, *, provider: str, model: str) -> AdminModelSnapshot:
        active = self.resolve_active(provider=provider, model=model)
        return AdminModelSnapshot(
            active_profile_id=active.profile_id,
            provider=active.provider,
            model=active.model,
            enabled_profile_ids=tuple(item.profile_id for item in self.enabled_profiles()),
        )
