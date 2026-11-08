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
    assert parse_tool_plan('[{"tool_id":"engineer.git.status","arguments":{}}]')[0].tool_id == "engineer.git.status"
    assert parse_tool_plan('"\\\\{\\\"tool_calls\\\":[]}"') == ()
    with pytest.raises(ValueError, match="vượt giới hạn"):
        parse_tool_plan('{"tool_calls":' + str([{"tool_id":"engineer.git.status","arguments":{}}] * 7) + '}')


def test_planner_parser_explains_unexpected_json_shapes():
    with pytest.raises(ValueError, match="thiếu trường 'tool_calls'"):
        parse_tool_plan('{"actions":[]}')
    with pytest.raises(ValueError, match="phải là danh sách"):
        parse_tool_plan('{"tool_calls":{"tool_id":"engineer.git.status"}}')
    with pytest.raises(ValueError, match="kiểu dữ liệu nhận được: str"):
        parse_tool_plan('"Không thể lập kế hoạch"')


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


def test_patch_rejects_src_parent_traversal_outside_allowed_directory(tmp_path: Path):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    outside = root / "outside.py"
    outside.write_text("VALUE = 1\\n", encoding="utf-8")
    agent = ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=object())
    original = outside.read_bytes()

    with pytest.raises(ValueError, match="đường dẫn chuẩn|bên trong src"):
        agent.prepare_patch([{
            "path": "src/../outside.py",
            "content": "VALUE = 2\\n",
            "expected_sha256": hashlib.sha256(original).hexdigest(),
        }], rationale="Reject parent traversal outside src.")

    assert outside.read_bytes() == original


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



def test_patch_preview_shows_diff_before_admin_approval(tmp_path: Path):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    source = root / "src" / "engine.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    agent = ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=object())
    prepared = agent.prepare_patch([{
        "path": "src/engine.py",
        "content": "VALUE = 2\n",
        "expected_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }], rationale="Preview test.")
    diff = agent.patch_preview(prepared["patch_id"])
    assert "--- a/src/engine.py" in diff
    assert "-VALUE = 1" in diff
    assert "+VALUE = 2" in diff
    assert source.read_text(encoding="utf-8") == "VALUE = 1\n"


def test_patch_preview_rejects_source_changed_after_proposal(tmp_path: Path):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    source = root / "src" / "engine.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    agent = ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=object())
    prepared = agent.prepare_patch([{
        "path": "src/engine.py",
        "content": "VALUE = 2\n",
        "expected_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }], rationale="Stale preview test.")
    source.write_text("VALUE = 3\n", encoding="utf-8")
    with pytest.raises(ValueError):
        agent.patch_preview(prepared["patch_id"])


def test_test_subprocess_does_not_inherit_admin_or_provider_secrets(monkeypatch):
    from ai_kernel.chief_engineer_agent import _safe_child_environment

    monkeypatch.setenv("PATH", "/safe/path")
    monkeypatch.setenv("OLLAMA_API_KEY", "ollama-secret-value")
    monkeypatch.setenv("MATH_TEACHER_AI_CHIEF_ENGINEER_ADMIN_TOKEN", "admin-secret-value")
    env = _safe_child_environment()
    assert env["PATH"] == "/safe/path"
    assert "OLLAMA_API_KEY" not in env
    assert "MATH_TEACHER_AI_CHIEF_ENGINEER_ADMIN_TOKEN" not in env
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"



def test_patch_failure_rolls_back_already_written_files(tmp_path: Path, monkeypatch):
    from ai_kernel import chief_engineer_agent as module

    root = _repo(tmp_path)
    first = root / "src" / "first.py"
    second = root / "src" / "second.py"
    first.write_text("FIRST = 1\n", encoding="utf-8")
    second.write_text("SECOND = 1\n", encoding="utf-8")
    originals = {first: first.read_bytes(), second: second.read_bytes()}
    agent = module.ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=object())
    prepared = agent.prepare_patch([
        {"path": "src/first.py", "content": "FIRST = 2\n",
         "expected_sha256": hashlib.sha256(originals[first]).hexdigest()},
        {"path": "src/second.py", "content": "SECOND = 2\n",
         "expected_sha256": hashlib.sha256(originals[second]).hexdigest()},
    ], rationale="Rollback test.")

    monkeypatch.setenv("MATH_TEACHER_AI_CHIEF_ENGINEER_ADMIN_TOKEN", "B" * 40)
    atomic_write = module._atomic_write_bytes
    failed_once = {"value": False}

    def fail_second_source_once(path, value, *, mode=None):
        if Path(path) == second and not failed_once["value"]:
            failed_once["value"] = True
            raise OSError("simulated second-file write failure")
        return atomic_write(path, value, mode=mode)

    monkeypatch.setattr(module, "_atomic_write_bytes", fail_second_source_once)
    with pytest.raises(RuntimeError):
        agent.approve_and_apply_patch(
            prepared["approval_id"],
            admin_actor="local-admin",
            admin_token="B" * 40,
            confirmation="APPLY PATCH " + prepared["approval_id"],
        )

    assert first.read_bytes() == originals[first]
    assert second.read_bytes() == originals[second]
    assert agent.patch_status(prepared["patch_id"])["status"] == "rolled_back"
    assert agent.approvals.get(prepared["approval_id"]).status.value == "failed"



def test_ai_drafts_patch_but_never_changes_source_before_approval(tmp_path: Path):
    import json
    from types import SimpleNamespace
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    source = root / "src" / "engine.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    original = source.read_bytes()

    class FakeKernelService:
        def run(self, **_kwargs):
            return SimpleNamespace(text=json.dumps({
                "changes": [{"path": "src/engine.py", "content": "VALUE = 2\n"}]
            }))

    agent = ChiefEngineerAgent(
        repo_root=root,
        state_dir=tmp_path / "state",
        service=FakeKernelService(),
    )
    result = agent.draft_patch(
        ["src/engine.py"],
        rationale="Cập nhật giá trị trong tệp thử nghiệm.",
    )
    assert result["generated_by_ai"] is True
    assert result["source_changed"] is False
    assert source.read_bytes() == original
    assert "-VALUE = 1" in agent.patch_preview(result["patch_id"])
    assert "+VALUE = 2" in agent.patch_preview(result["patch_id"])


def test_ai_draft_cannot_escape_selected_source_files(tmp_path: Path):
    import json
    from types import SimpleNamespace
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    source = root / "src" / "engine.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    class FakeKernelService:
        def run(self, **_kwargs):
            return SimpleNamespace(text=json.dumps({
                "changes": [{"path": "../outside.py", "content": "VALUE = 2\n"}]
            }))

    agent = ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=FakeKernelService())
    with pytest.raises(ValueError):
        agent.draft_patch(["src/engine.py"], rationale="Path allowlist.")
    assert source.read_text(encoding="utf-8") == "VALUE = 1\n"



def test_agent_resumes_approved_but_unclaimed_patch(tmp_path: Path, monkeypatch):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent
    from ai_kernel.contracts import AIOwnership

    root = _repo(tmp_path)
    source = root / "src" / "engine.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    original = source.read_bytes()
    agent = ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=object())
    prepared = agent.prepare_patch([{
        "path": "src/engine.py",
        "content": "VALUE = 2\n",
        "expected_sha256": hashlib.sha256(original).hexdigest(),
    }], rationale="Resume approved patch test.")

    agent.approvals.approve(
        prepared["approval_id"],
        admin_actor="local-admin",
        actor_owner=AIOwnership.ADMIN,
    )
    monkeypatch.setenv("MATH_TEACHER_AI_CHIEF_ENGINEER_ADMIN_TOKEN", "C" * 40)
    run = agent.approve_and_apply_patch(
        prepared["approval_id"],
        admin_actor="local-admin",
        admin_token="C" * 40,
        confirmation="APPLY PATCH " + prepared["approval_id"],
    )
    assert run.status.value == "completed"
    assert source.read_text(encoding="utf-8") == "VALUE = 2\n"



def test_cli_approval_id_resolves_patch_id_for_preview_and_apply(tmp_path: Path, monkeypatch, capsys):
    from types import SimpleNamespace
    from ai_kernel import chief_engineer_agent as module

    approval_id = "approval-123"
    patch_id = "a" * 32
    calls = {}

    class FakeAgent:
        def __init__(self, **_kwargs):
            self.approvals = SimpleNamespace(get=lambda _approval_id: SimpleNamespace(
                tool_id=module.PATCH_APPLY_TOOL,
                skill_id=module.PATCH_SKILL_ID,
                arguments={"patch_id": patch_id},
            ))

        def _load_patch_manifest(self, selected_patch_id):
            assert selected_patch_id == patch_id
            return {"approval_id": approval_id}

        def patch_preview(self, selected_patch_id):
            calls["preview"] = selected_patch_id
            return "FULL DIFF"

        def approve_and_apply_patch(self, selected_approval_id, **kwargs):
            calls["apply"] = (selected_approval_id, kwargs)
            return SimpleNamespace(run_id="run-1", status=SimpleNamespace(value="completed"))

        def patch_status(self, selected_patch_id):
            calls["status"] = selected_patch_id
            return {"patch_id": selected_patch_id, "status": "applied"}

    monkeypatch.setattr(module, "ChiefEngineerAgent", FakeAgent)
    monkeypatch.setattr(module, "input", lambda _prompt: "APPLY PATCH " + approval_id, raising=False)
    monkeypatch.setattr(module.getpass, "getpass", lambda _prompt: "local-admin-token")

    result = module.main([
        "--repo-root", str(tmp_path),
        "--approve-approval-id", approval_id,
        "--admin-actor", "local-admin",
    ])

    output = capsys.readouterr().out
    assert result == 0
    assert "FULL DIFF" in output
    assert calls["preview"] == patch_id
    assert calls["apply"][0] == approval_id
    assert calls["status"] == patch_id


def test_no_tests_mode_removes_pytest_tool_from_registry(tmp_path: Path):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    agent = ChiefEngineerAgent(
        repo_root=root,
        state_dir=tmp_path / "state-no-tests",
        service=object(),
        allow_tests=False,
    )
    tool_ids = {spec.tool_id for spec in agent.tools.specs()}
    assert "engineer.tests.run_pytest" not in tool_ids
    assert "engineer.git.status" in tool_ids
    assert "engineer.repo.inventory" in tool_ids



def test_patch_preview_refuses_to_truncate_long_diff(tmp_path: Path):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    source = root / "src" / "large_module.py"
    original_text = "".join(f"VALUE_{index:04d} = 1\n" for index in range(1400))
    changed_text = "".join(f"VALUE_{index:04d} = 2\n" for index in range(1400))
    source.write_text(original_text, encoding="utf-8")
    agent = ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=object())
    proposal = agent.prepare_patch([{
        "path": "src/large_module.py",
        "content": changed_text,
        "expected_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }], rationale="Test full diff visibility.")
    with pytest.raises(ValueError, match="chia bản vá"):
        agent.patch_preview(proposal["patch_id"])
    assert source.read_text(encoding="utf-8") == original_text


def test_patch_refuses_source_containing_recognized_secret(tmp_path: Path):
    from ai_kernel.chief_engineer_agent import ChiefEngineerAgent

    root = _repo(tmp_path)
    source = root / "src" / "ordinary_module.py"
    original = 'API_KEY = "this-is-a-test-secret-value-12345"\n'
    source.write_text(original, encoding="utf-8")
    agent = ChiefEngineerAgent(repo_root=root, state_dir=tmp_path / "state", service=object())
    with pytest.raises(ValueError, match="khóa bí mật"):
        agent.prepare_patch([{
            "path": "src/ordinary_module.py",
            "content": "VALUE = 2\n",
            "expected_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }], rationale="Must reject source with embedded credentials.")
