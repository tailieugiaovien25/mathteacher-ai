from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

from ai_kernel import AIOwnership, AIRuntimeManager, JSONAIRuntimeConfigStore
from ai_kernel.governance import AdminPolicyError
from ai_kernel.profiles import default_model_profiles

ROOT = Path(__file__).resolve().parents[1]


def _manager(tmp_path: Path) -> AIRuntimeManager:
    return AIRuntimeManager(
        profiles=default_model_profiles(),
        store=JSONAIRuntimeConfigStore(tmp_path / "runtime.json"),
        provider="ollama",
        base_url="http://127.0.0.1:11434",
    )


def test_runtime_bootstrap_has_active_and_allowlist(tmp_path: Path):
    manager = _manager(tmp_path)
    config = manager.config()
    assert config.active_profile_id
    assert config.active_profile_id in config.enabled_profile_ids
    assert manager.active_profile().provider == "ollama"


def test_only_admin_can_change_runtime(tmp_path: Path):
    manager = _manager(tmp_path)
    with pytest.raises(AdminPolicyError):
        manager.set_active_profile(manager.config().active_profile_id, owner=AIOwnership.USER, admin_actor="teacher")


def test_admin_can_change_active_and_persist(tmp_path: Path):
    manager = _manager(tmp_path)
    manager.set_active_profile("deepseek-r1-reasoning", owner=AIOwnership.ADMIN, admin_actor="admin-1")
    assert manager.config().active_profile_id == "deepseek-r1-reasoning"
    restored = AIRuntimeManager(
        profiles=default_model_profiles(),
        store=JSONAIRuntimeConfigStore(tmp_path / "runtime.json"),
    )
    assert restored.config().active_profile_id == "deepseek-r1-reasoning"


def test_cannot_disable_active_profile(tmp_path: Path):
    manager = _manager(tmp_path)
    active = manager.config().active_profile_id
    remaining = [pid for pid in manager.config().enabled_profile_ids if pid != active]
    with pytest.raises(AdminPolicyError):
        manager.set_enabled_profiles(remaining, owner=AIOwnership.ADMIN, admin_actor="admin-1")


def test_runtime_center_is_registered_for_admin_only():
    nav = ROOT / "portal_v2" / "ui" / "admin_navigation.py"
    text = nav.read_text(encoding="utf-8")
    assert 'ADMIN_PAGE_AI_RUNTIME_CENTER = "ai_runtime_center"' in text
    assert '"AI Runtime & Model Center"' in text
    routes = ROOT / "portal_v2" / "ui" / "workspace_navigation.py"
    assert '"ai_runtime_center": "Vận hành"' in routes.read_text(encoding="utf-8")
    shell = ROOT / "portal_v2" / "ui" / "admin_shell.py"
    shell_text = shell.read_text(encoding="utf-8")
    assert "render_admin_ai_runtime_center" in shell_text
