from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ai_platform.providers.ollama import OllamaProvider

from .contracts import AIOwnership
from .governance import AdminPolicyError, AIKernelGovernance
from .profiles import ModelProfile, default_model_profiles


@dataclass(frozen=True)
class AIRuntimeConfig:
    """ADMIN-owned runtime configuration; the AI Kernel itself remains immutable."""

    provider: str
    base_url: str
    active_profile_id: str
    enabled_profile_ids: tuple[str, ...]
    fallback_profile_ids: tuple[str, ...] = ()
    updated_at: str = ""


@dataclass(frozen=True)
class AIRuntimeStatus:
    provider: str
    base_url: str
    reachable: bool
    active_profile_id: str
    active_model: str
    active_model_installed: bool
    local_models: tuple[str, ...] = ()
    message: str = ""


class JSONAIRuntimeConfigStore:
    """Local-first persistence for ADMIN runtime configuration."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path or os.getenv("MATH_TEACHER_AI_RUNTIME_CONFIG", ".mathteacher_ai/runtime_config.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AIRuntimeConfig | None:
        if not self.path.exists():
            return None
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        try:
            return AIRuntimeConfig(
                provider=str(raw.get("provider") or "ollama"),
                base_url=str(raw.get("base_url") or "http://127.0.0.1:11434"),
                active_profile_id=str(raw.get("active_profile_id") or ""),
                enabled_profile_ids=tuple(str(item) for item in raw.get("enabled_profile_ids") or ()),
                fallback_profile_ids=tuple(str(item) for item in raw.get("fallback_profile_ids") or ()),
                updated_at=str(raw.get("updated_at") or ""),
            )
        except (AttributeError, TypeError, ValueError):
            return None

    def save(self, config: AIRuntimeConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="runtime-config-", suffix=".json", dir=self.path.parent)
        payload = asdict(config)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


class AIRuntimeManager:
    """ADMIN gate for local AI runtime selection and allow-listing.

    It can inspect a runtime and change only the ADMIN-owned configuration layer.
    It never pulls/deletes models and never mutates the AI Kernel or governance.
    """

    def __init__(
        self,
        *,
        profiles: Iterable[ModelProfile] | None = None,
        governance: AIKernelGovernance | None = None,
        store: JSONAIRuntimeConfigStore | None = None,
        provider: str = "ollama",
        base_url: str = "http://127.0.0.1:11434",
        selected_profile_id: str = "",
    ) -> None:
        self.profiles = tuple(profiles or default_model_profiles())
        self._by_id = {item.profile_id: item for item in self.profiles}
        self.governance = governance or AIKernelGovernance()
        self.store = store or JSONAIRuntimeConfigStore()
        self._bootstrap(provider=provider, base_url=base_url, selected_profile_id=selected_profile_id)

    def _bootstrap(self, *, provider: str, base_url: str, selected_profile_id: str) -> None:
        current = self.store.load()
        if current is not None:
            self._config = self._sanitize(current)
            return
        enabled = tuple(item.profile_id for item in self.profiles if item.admin_enabled)
        candidate = self._profile_for_provider_model(provider=provider, model="")
        active = selected_profile_id if selected_profile_id in enabled else (candidate.profile_id if candidate else (enabled[0] if enabled else ""))
        self._config = AIRuntimeConfig(
            provider=str(provider or "ollama"),
            base_url=str(base_url or "http://127.0.0.1:11434").rstrip("/"),
            active_profile_id=active,
            enabled_profile_ids=enabled,
            fallback_profile_ids=tuple(item for item in enabled if item != active),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _sanitize(self, config: AIRuntimeConfig) -> AIRuntimeConfig:
        enabled = tuple(pid for pid in config.enabled_profile_ids if pid in self._by_id and self._by_id[pid].admin_enabled)
        if not enabled:
            enabled = tuple(item.profile_id for item in self.profiles if item.admin_enabled)
        active = config.active_profile_id if config.active_profile_id in enabled else (enabled[0] if enabled else "")
        fallback = tuple(pid for pid in config.fallback_profile_ids if pid in enabled and pid != active)
        return AIRuntimeConfig(
            provider=config.provider or "ollama",
            base_url=config.base_url.rstrip("/") or "http://127.0.0.1:11434",
            active_profile_id=active,
            enabled_profile_ids=enabled,
            fallback_profile_ids=fallback,
            updated_at=config.updated_at,
        )

    def _profile_for_provider_model(self, *, provider: str, model: str) -> ModelProfile | None:
        provider_norm = str(provider or "").strip().casefold()
        model_norm = str(model or "").strip()
        for profile in self.profiles:
            if not profile.admin_enabled or profile.provider.casefold() != provider_norm:
                continue
            if model_norm and profile.model != model_norm:
                continue
            return profile
        return None

    def _require_admin(self, owner: AIOwnership) -> None:
        self.governance.authorize_configuration(owner)

    def config(self) -> AIRuntimeConfig:
        return self._config

    def resolve_profile(self, profile_id: str) -> ModelProfile:
        normalized = str(profile_id or "").strip()
        try:
            profile = self._by_id[normalized]
        except KeyError as exc:
            raise AdminPolicyError(f"Không tìm thấy model profile: {normalized}") from exc
        if not profile.admin_enabled:
            raise AdminPolicyError(f"Model profile chưa được ADMIN bật: {normalized}")
        return profile

    def active_profile(self) -> ModelProfile:
        return self.resolve_profile(self._config.active_profile_id)

    def enabled_profiles(self) -> tuple[ModelProfile, ...]:
        return tuple(self._by_id[pid] for pid in self._config.enabled_profile_ids if pid in self._by_id and self._by_id[pid].admin_enabled)

    def fallback_profiles(self) -> tuple[ModelProfile, ...]:
        return tuple(self._by_id[pid] for pid in self._config.fallback_profile_ids if pid in self._by_id)

    def set_active_profile(self, profile_id: str, *, owner: AIOwnership, admin_actor: str) -> AIRuntimeConfig:
        self._require_admin(owner)
        if not str(admin_actor).strip():
            raise AdminPolicyError("ADMIN actor là bắt buộc.")
        profile_id = str(profile_id).strip()
        profile = self._by_id.get(profile_id)
        if profile is None or not profile.admin_enabled:
            raise AdminPolicyError(f"Model profile chưa được ADMIN bật: {profile_id}")
        enabled = list(self._config.enabled_profile_ids)
        if profile_id not in enabled:
            enabled.append(profile_id)
        fallback = tuple(pid for pid in self._config.fallback_profile_ids if pid != profile_id and pid in enabled)
        self._config = AIRuntimeConfig(
            provider=profile.provider,
            base_url=self._config.base_url,
            active_profile_id=profile_id,
            enabled_profile_ids=tuple(enabled),
            fallback_profile_ids=fallback,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.store.save(self._config)
        return self._config

    def set_enabled_profiles(self, profile_ids: Iterable[str], *, owner: AIOwnership, admin_actor: str) -> AIRuntimeConfig:
        self._require_admin(owner)
        if not str(admin_actor).strip():
            raise AdminPolicyError("ADMIN actor là bắt buộc.")
        normalized = tuple(dict.fromkeys(str(pid).strip() for pid in profile_ids if str(pid).strip()))
        if not normalized:
            raise AdminPolicyError("Phải còn ít nhất một model profile được bật.")
        unknown = [pid for pid in normalized if pid not in self._by_id or not self._by_id[pid].admin_enabled]
        if unknown:
            raise AdminPolicyError(f"Profile không hợp lệ: {', '.join(unknown)}")
        if self._config.active_profile_id not in normalized:
            raise AdminPolicyError("Không thể tắt profile đang hoạt động; hãy chọn active profile trước.")
        fallback = tuple(pid for pid in self._config.fallback_profile_ids if pid in normalized and pid != self._config.active_profile_id)
        self._config = AIRuntimeConfig(
            provider=self._config.provider,
            base_url=self._config.base_url,
            active_profile_id=self._config.active_profile_id,
            enabled_profile_ids=normalized,
            fallback_profile_ids=fallback,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.store.save(self._config)
        return self._config

    def set_fallback_profiles(self, profile_ids: Iterable[str], *, owner: AIOwnership, admin_actor: str) -> AIRuntimeConfig:
        self._require_admin(owner)
        if not str(admin_actor).strip():
            raise AdminPolicyError("ADMIN actor là bắt buộc.")
        normalized = tuple(dict.fromkeys(str(pid).strip() for pid in profile_ids if str(pid).strip()))
        invalid = [pid for pid in normalized if pid not in self._config.enabled_profile_ids or pid == self._config.active_profile_id]
        if invalid:
            raise AdminPolicyError("Fallback phải là profile đang bật và khác active profile.")
        self._config = AIRuntimeConfig(
            provider=self._config.provider,
            base_url=self._config.base_url,
            active_profile_id=self._config.active_profile_id,
            enabled_profile_ids=self._config.enabled_profile_ids,
            fallback_profile_ids=normalized,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.store.save(self._config)
        return self._config

    def inspect_runtime(self) -> AIRuntimeStatus:
        active = self.active_profile()
        if active.provider != "ollama":
            return AIRuntimeStatus(
                provider=active.provider,
                base_url=self._config.base_url,
                reachable=False,
                active_profile_id=active.profile_id,
                active_model=active.model,
                active_model_installed=False,
                message="Provider hiện tại chưa có runtime inspector local.",
            )
        provider = OllamaProvider(base_url=self._config.base_url, model=active.model)
        reachable = provider.health()
        if not reachable:
            return AIRuntimeStatus(
                provider="ollama",
                base_url=self._config.base_url,
                reachable=False,
                active_profile_id=active.profile_id,
                active_model=active.model,
                active_model_installed=False,
                message="Không kết nối được Ollama local.",
            )
        try:
            local_models = provider.list_models()
        except Exception as exc:
            return AIRuntimeStatus(
                provider="ollama",
                base_url=self._config.base_url,
                reachable=True,
                active_profile_id=active.profile_id,
                active_model=active.model,
                active_model_installed=False,
                message=f"Ollama có phản hồi nhưng không đọc được danh sách model: {exc}",
            )
        installed = active.model in local_models
        return AIRuntimeStatus(
            provider="ollama",
            base_url=self._config.base_url,
            reachable=True,
            active_profile_id=active.profile_id,
            active_model=active.model,
            active_model_installed=installed,
            local_models=local_models,
            message="Model active đã cài đặt." if installed else "Model active chưa được cài đặt local.",
        )
