from __future__ import annotations

from pathlib import Path
import hashlib

import pytest

from ai_kernel.chief_engineer_agent import (
    chief_engineer_tool_specs,
    parse_tool_plan,
    redact_sensitive_text,
    repository_inventory,
    resolve_repository_file,
    validate_test_targets,
)
from ai_kernel.contracts import AIActionClass


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "src" / "tests").mkdir(parents=True)
    (root / "src" / "tests" / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    (root / "README.md").write_text("safe docs\n", encoding="utf-8")
    (root / ".env").write_text("API_KEY=do-not-read\n", encoding="utf-8")
    return root


def test_file_reader_allows_source_but_denies_env_and_traversal(tmp_path: Path):
    root = _repo(tmp_path)
    assert resolve_repository_file(root, "README.md").name == "README.md"
    with pytest.raises(ValueError):
        resolve_repository_file(root, ".env")
    with pytest.raises(ValueError):
        resolve_repository_file(root, "../outside.py")


def test_file_reader_denies_non_allowlisted_extensions(tmp_path: Path):
    root = _repo(tmp_path)
    (root / "settings.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        resolve_repository_file(root, "settings.json")


def test_inventory_excludes_git_and_env_material(tmp_path: Path):
    root = _repo(tmp_path)
    result = repository_inventory(root)
    assert result["files_counted"] == 2
    assert ".env" not in str(result)
    assert ".git" not in str(result)


def test_test_runner_only_accepts_explicit_project_test_files(tmp_path: Path):
    root = _repo(tmp_path)
    assert validate_test_targets(root, ["src/tests/test_sample.py"]) == ["src/tests/test_sample.py"]
    with pytest.raises(ValueError):
        validate_test_targets(root, ["README.md"])
    with pytest.raises(ValueError):
        validate_test_targets(root, ["src/tests/test_sample.py"] * 6)


def test_planner_json_is_parsed_and_bounded():
    calls = parse_tool_plan('{"tool_calls":[{"tool_id":"engineer.git.status","arguments":{}}]}')
    assert len(calls) == 1
    assert calls[0].tool_id == "engineer.git.status"
    assert parse_tool_plan("```json\n{\"tool_calls\": []}\n```") == ()
    with pytest.raises(ValueError):
        parse_tool_plan('{"tool_calls":' + str([{}] * 7) + '}')


def test_tool_allowlist_has_no_write_or_governance_action():
    specs = chief_engineer_tool_specs()
    assert specs
    assert all(AIActionClass.MUTATING not in spec.allowed_actions for spec in specs)
    assert all(AIActionClass.GOVERNANCE not in spec.allowed_actions for spec in specs)


def test_secret_scrubber_does_not_emit_common_credentials():
    raw = "API_KEY=example-secret-value\nAuthorization: Bearer abcdefghijklmnopqrstuvwxyz012345\nghp_abcdefghijklmnopqrstuvwxyz012345"
    cleaned = redact_sensitive_text(raw)
    assert "example-secret-value" not in cleaned
    assert "abcdefghijklmnopqrstuvwxyz012345" not in cleaned
    assert "ghp_" not in cleaned
    assert "[REDACTED]" in cleaned


def test_chief_engineer_agent_completes_a_bounded_read_only_cycle(tmp_path: Path):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)

    class FakeKernelService:
        def __init__(self):
            self.calls = 0

        def run(self, **_kwargs):
            from types import SimpleNamespace

            self.calls += 1
            if self.calls == 1:
                return SimpleNamespace(text='{"tool_calls":[{"tool_id":"engineer.repo.inventory","arguments":{}}]}')
            return SimpleNamespace(text='{"tool_calls":[]}')

    state_dir = tmp_path / "agent-state"
    agent = ChiefEngineerAgent(
        repo_root=root,
        state_dir=state_dir,
        service=FakeKernelService(),
        max_cycles=3,
    )
    run = agent.run("Kiểm tra cấu trúc repository trong môi trường thử nghiệm.")

    assert run.status.value == "completed"
    assert run.cycle_count == 2
    assert any(row.get("tool_id") == "engineer.repo.inventory" for row in agent.observations)
    assert (state_dir / "agent_runs.json").is_file()
    assert (state_dir / "autonomous_runs.json").is_file()
    assert (root / "README.md").read_text(encoding="utf-8") == "safe docs\n"


def test_patch_requires_confirmation_and_admin_token_then_backs_up(tmp_path: Path, monkeypatch):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    source = root / "src" / "engine.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    original = source.read_bytes()
    agent = ChiefEngineerAgent(
        repo_root=root,
        state_dir=tmp_path / "chief-state",
        service=object(),
    )
    prepared = agent.prepare_patch(
        [{
            "path": "src/engine.py",
            "content": "VALUE = 2\n",
            "expected_sha256": hashlib.sha256(original).hexdigest(),
        }],
        rationale="Sửa lỗi giá trị trong mô-đun thử nghiệm.",
    )
    assert source.read_bytes() == original
    assert prepared["source_changed"] is False

    monkeypatch.setenv("MATH_TEACHER_AI_CHIEF_ENGINEER_ADMIN_TOKEN", "A" * 40)
    with pytest.raises(ValueError):
        agent.approve_and_apply_patch(
            prepared["approval_id"],
            admin_actor="local-admin",
            admin_token="A" * 40,
            confirmation="wrong confirmation",
        )
    with pytest.raises(PermissionError):
        agent.approve_and_apply_patch(
            prepared["approval_id"],
            admin_actor="local-admin",
            admin_token="wrong-token",
            confirmation="APPLY PATCH " + prepared["approval_id"],
        )
    assert source.read_bytes() == original
    assert agent.approvals.get(prepared["approval_id"]).status.value == "pending"

    run = agent.approve_and_apply_patch(
        prepared["approval_id"],
        admin_actor="local-admin",
        admin_token="A" * 40,
        confirmation="APPLY PATCH " + prepared["approval_id"],
    )
    assert run.status.value == "completed"
    assert source.read_text(encoding="utf-8") == "VALUE = 2\n"
    patch_status = agent.patch_status(prepared["patch_id"])
    assert patch_status["status"] == "applied"
    backup = tmp_path / "chief-state" / patch_status["backups"][0]["backup_path"]
    assert backup.read_bytes() == original
    assert agent.approvals.get(prepared["approval_id"]).status.value == "executed"


def test_patch_rejects_stale_hash_path_escape_and_invalid_python(tmp_path: Path):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    source = root / "src" / "engine.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    agent = ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=object())
    actual = hashlib.sha256(source.read_bytes()).hexdigest()

    with pytest.raises(ValueError):
        agent.prepare_patch([{
            "path": "src/engine.py",
            "content": "VALUE = 2\n",
            "expected_sha256": "0" * 64,
        }], rationale="Stale hash.")
    with pytest.raises(ValueError):
        agent.prepare_patch([{
            "path": "../outside.py",
            "content": "VALUE = 2\n",
            "expected_sha256": actual,
        }], rationale="Path traversal.")
    with pytest.raises(ValueError):
        agent.prepare_patch([{
            "path": "src/engine.py",
            "content": "def broken(:\n",
            "expected_sha256": actual,
        }], rationale="Syntax validation.")


def test_patch_rejects_secret_like_content_and_does_not_change_source(tmp_path: Path):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    source = root / "src" / "engine.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    original = source.read_bytes()
    agent = ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=object())

    with pytest.raises(ValueError):
        agent.prepare_patch([{
            "path": "src/engine.py",
            "content": 'API_KEY = "example-secret-value-12345"\n',
            "expected_sha256": hashlib.sha256(original).hexdigest(),
        }], rationale="Must not persist credentials.")

    assert source.read_bytes() == original
