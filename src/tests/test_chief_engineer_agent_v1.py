from __future__ import annotations

from pathlib import Path

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
