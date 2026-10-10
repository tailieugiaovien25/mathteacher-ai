from __future__ import annotations

from ai_platform.config import AIPlatformConfig
from ai_platform.contracts import AIRequest, AIResponse
from ai_platform.marketing.service import MarketingAIService
from ai_platform.system_admin.service import SystemAdminAIService


class FakeProvider:
    provider_id = "fake"
    model = "test"

    def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(
            text=f"ok:{request.task}",
            provider=self.provider_id,
            model=self.model,
        )


def test_marketing_is_disabled_by_default():
    config = AIPlatformConfig(commercial_mode=False, marketing_enabled=True)
    service = MarketingAIService(FakeProvider(), config)
    assert service.enabled() is False


def test_marketing_requires_commercial_mode():
    config = AIPlatformConfig(commercial_mode=True, marketing_enabled=True)
    service = MarketingAIService(FakeProvider(), config)
    assert service.draft(
        objective="launch",
        audience="teachers",
        channel="website",
    ) == "ok:marketing_draft"


def test_system_admin_is_read_only_contract():
    config = AIPlatformConfig(system_admin_enabled=True)
    service = SystemAdminAIService(FakeProvider(), config)
    diagnostic = service.diagnose(({"name": "db", "status": "ok"},))
    assert diagnostic.checks[0]["status"] == "ok"
    assert service.explain(diagnostic) == "ok:system_diagnostics"


def test_provider_config_defaults_to_ollama(monkeypatch):
    monkeypatch.delenv("MATH_TEACHER_AI_PROVIDER", raising=False)
    config = AIPlatformConfig.from_environment()
    assert config.provider == "ollama"
    assert config.marketing_runtime_enabled is False


def test_navigation_contains_new_ai_groups():
    from pathlib import Path
    nav = Path(__file__).resolve().parents[1] / "portal_v2" / "ui" / "admin_navigation.py"
    text = nav.read_text(encoding="utf-8-sig")
    assert 'ADMIN_PAGE_SYSTEM_ADMIN_AI = "system_admin_ai"' in text
    assert 'ADMIN_PAGE_MARKETING_AI = "marketing_ai"' in text

def test_group_module_registries_are_complete():
    from ai_platform.system_admin.modules import SYSTEM_ADMIN_MODULES
    from ai_platform.marketing.modules import MARKETING_MODULES
    assert len(SYSTEM_ADMIN_MODULES) == 7
    assert len(MARKETING_MODULES) == 8
    assert all(item.mode in {"read_only", "human_approved", "draft"} for item in SYSTEM_ADMIN_MODULES + MARKETING_MODULES)
