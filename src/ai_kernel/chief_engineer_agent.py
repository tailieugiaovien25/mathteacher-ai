"""Chief Engineer Agent V1: repository inspection and selected test runner."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from .agent_planner import SafeAgentPlanner
from .agent_runtime import AIToolCall, AIToolRegistry, AIToolSpec, JSONAgentRunStore, SafeAgentRuntime
from .approval_queue import ApprovalQueue, JSONApprovalQueueStore
from .autonomous_orchestrator import AutonomousOrchestrator, JSONAutonomousRunStore
from .contracts import AIActionClass, AIOwnership
from .skills import default_ai_skills

EXCLUDED = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mathteacher_ai", "secrets", "credentials", "private", "keys"})
READABLE = frozenset({".py", ".md", ".toml", ".yml", ".yaml"})
SENSITIVE = ("secret", "credential", "password", "token", "private_key")
MAX_FILE_BYTES = 49152


def redact_sensitive_text(value: object) -> str:
    """Remove credential-bearing lines and truncate opaque token-bearing output."""
    labels = ("api_key", "api-key", "client_secret", "client-secret", "secret", "password",
              "token", "access_token", "access-token", "refresh_token", "refresh-token")
    token_markers = ("ghp_", "gho_", "ghs_", "ghu_", "ghr_", "sk-", "Bearer ")
    safe_lines = []
    for line in str(value or "").splitlines():
        lowered = line.casefold()
        positions = [line.find(mark) for mark in (":", "=") if line.find(mark) >= 0]
        if any(label in lowered for label in labels) and positions:
            cut = min(positions)
            safe_lines.append(line[:cut + 1] + " [REDACTED]")
            continue
        marker_positions = [line.find(mark) for mark in token_markers if line.find(mark) >= 0]
        if marker_positions:
            safe_lines.append(line[:min(marker_positions)] + "[REDACTED]")
        else:
            safe_lines.append(line)
    return "\n".join(safe_lines)[:12000]

def _sensitive(path: Path) -> bool:
    parts = [part.casefold() for part in path.parts]
    name = path.name.casefold()
    return (
        any(part in EXCLUDED for part in parts)
        or name.startswith(".env") or name in {"id_rsa", "id_ed25519"}
        or any(marker in name for marker in SENSITIVE)
        or path.suffix.casefold() in {".pem", ".key", ".p12", ".pfx", ".keystore"}
    )


def resolve_repository_file(root: Path, relative: object) -> Path:
    raw = str(relative or "").strip()
    if not raw or chr(0) in raw:
        raise ValueError("Đường dẫn không hợp lệ.")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ValueError("Chỉ chấp nhận đường dẫn tương đối.")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        safe_relative = resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("Đường dẫn vượt ra ngoài repository.") from exc
    if _sensitive(safe_relative):
        raise ValueError("Từ chối truy cập đường dẫn có khả năng chứa dữ liệu bí mật.")
    if not resolved.is_file():
        raise FileNotFoundError(safe_relative.as_posix())
    if resolved.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Tệp vượt giới hạn đọc.")
    if resolved.suffix.casefold() not in READABLE:
        raise ValueError("Định dạng tệp chưa được cho phép.")
    return resolved


def _command(argv: list[str], root: Path, timeout: int) -> dict[str, Any]:
    try:
        result = subprocess.run(
            argv, cwd=str(root), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            timeout=timeout, shell=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False,
        )
        return {"returncode": result.returncode, "output": redact_sensitive_text(result.stdout), "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return {"returncode": None, "output": redact_sensitive_text(output + " Lệnh vượt thời gian."), "timed_out": True}
    except OSError as exc:
        return {"returncode": None, "output": "Không chạy được công cụ: " + type(exc).__name__, "timed_out": False}


def repository_inventory(root: Path, limit: int = 5000) -> dict[str, Any]:
    extensions, folders = Counter(), Counter()
    count, truncated = 0, False
    for current, directories, filenames in os.walk(root, followlinks=False):
        parent = Path(current)
        directories[:] = [name for name in directories if name.casefold() not in EXCLUDED and not (parent / name).is_symlink()]
        for filename in filenames:
            path = parent / filename
            try:
                relative = path.relative_to(root)
            except ValueError:
                continue
            if _sensitive(relative) or path.is_symlink():
                continue
            count += 1
            extensions[path.suffix.casefold() or "[no extension]"] += 1
            folders[relative.parts[0] if relative.parts else "[root]"] += 1
            if count >= limit:
                truncated = True
                break
        if truncated:
            break
    return {"files_counted": count, "truncated": truncated,
            "by_extension": dict(extensions.most_common(20)),
            "by_top_level": dict(folders.most_common(20))}


def validate_test_targets(root: Path, paths: object) -> list[str]:
    if not isinstance(paths, (list, tuple)) or not paths or len(paths) > 5:
        raise ValueError("Cần chỉ định từ 1 đến 5 tệp kiểm thử.")
    targets = []
    for value in paths:
        path = resolve_repository_file(root, value)
        relative = path.relative_to(root).as_posix()
        if not relative.startswith("src/tests/") or not path.name.startswith("test_") or path.suffix != ".py":
            raise ValueError("Chỉ cho phép test_*.py trong src/tests/.")
        targets.append(relative)
    return targets


def parse_tool_plan(raw: object, max_calls: int = 6) -> tuple[AIToolCall, ...]:
    source = str(raw or "").strip()
    if source.startswith("```"):
        lines = source.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        source = "\\n".join(lines).strip()
    payload = json.loads(source)
    if not isinstance(payload, dict) or not isinstance(payload.get("tool_calls", []), list):
        raise ValueError("Kế hoạch AI không đúng cấu trúc JSON.")
    rows = payload.get("tool_calls", [])
    if len(rows) > max_calls:
        raise ValueError("Kế hoạch vượt giới hạn số bước.")
    calls = []
    for row in rows:
        if not isinstance(row, dict) or set(row) - {"tool_id", "arguments"}:
            raise ValueError("Tool call không hợp lệ.")
        tool_id, arguments = row.get("tool_id"), row.get("arguments", {})
        if not isinstance(tool_id, str) or not tool_id.strip() or not isinstance(arguments, dict):
            raise ValueError("Tool ID hoặc arguments không hợp lệ.")
        calls.append(AIToolCall(tool_id.strip(), arguments))
    return tuple(calls)


def chief_engineer_tool_specs() -> tuple[AIToolSpec, ...]:
    safe = frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY})
    return (
        AIToolSpec("engineer.git.status", "Git status", "Đọc trạng thái Git.", safe, ("coding", "repository")),
        AIToolSpec("engineer.git.diff_summary", "Git diff summary", "Đọc thống kê thay đổi.", safe, ("coding", "repository")),
        AIToolSpec("engineer.repo.inventory", "Repository inventory", "Thống kê cấu trúc tệp; loại trừ vùng bí mật.", safe, ("coding", "repository")),
        AIToolSpec("engineer.repo.read_file", "Read source file", "Đọc mã nguồn/tài liệu trong allow-list.", safe, ("coding", "repository")),
        AIToolSpec("engineer.tests.run_pytest", "Run selected tests", "Chạy tối đa 5 test file cụ thể.", safe, ("coding", "testing")),
    )


class ChiefEngineerAgent:
    """Model-planned repo observer built on SafeAgentPlanner/Runtime/Orchestrator."""
    SKILL_ID = "system_admin.observer"

    def __init__(self, *, repo_root: str | os.PathLike[str], service: Any | None = None,
                 state_dir: str | os.PathLike[str] | None = None, timeout: int = 90,
                 max_cycles: int = 4, max_steps: int = 6):
        self.root = Path(repo_root).expanduser().resolve()
        if not self.root.is_dir() or not (self.root / ".git").exists():
            raise ValueError("repo_root phải là Git repository.")
        self.timeout = min(max(int(timeout), 5), 300)
        self.max_cycles = min(max(int(max_cycles), 1), 8)
        self.max_steps = min(max(int(max_steps), 1), 12)
        self.state_dir = Path(state_dir).resolve() if state_dir else self.root / ".mathteacher_ai" / "chief_engineer"
        if self.state_dir == self.root or (self.root in self.state_dir.parents and self.state_dir != self.root / ".mathteacher_ai" / "chief_engineer"):
            raise ValueError("state_dir trong repo chỉ được phép là .mathteacher_ai/chief_engineer.")
        self.service = service
        self.observations: list[dict[str, Any]] = []
        self.approvals = ApprovalQueue(JSONApprovalQueueStore(self.state_dir / "approvals.json"))
        skills = default_ai_skills()
        self.tools = AIToolRegistry(chief_engineer_tool_specs())
        self._bind_tools()
        self.runtime = SafeAgentRuntime(skills=skills, tools=self.tools,
            store=JSONAgentRunStore(self.state_dir / "agent_runs.json"),
            approval_queue=self.approvals, default_max_steps=self.max_steps)
        self.planner = SafeAgentPlanner(skills=skills, tools=self.tools,
            approval_queue=self.approvals, max_steps=self.max_steps)
        self.orchestrator = AutonomousOrchestrator(planner=self.planner, runtime=self.runtime,
            approval_queue=self.approvals,
            store=JSONAutonomousRunStore(self.state_dir / "autonomous_runs.json"),
            max_cycles=self.max_cycles, observation_provider=self._observe)

    def _record(self, tool_id: str, handler):
        def execute(args):
            result = handler(args)
            self.observations.append({"tool_id": tool_id, "result": result})
            return result
        return execute

    def _bind_tools(self):
        root, timeout = self.root, self.timeout
        self.tools.bind("engineer.git.status", self._record("engineer.git.status", lambda _a: _command(["git", "status", "--short", "--branch"], root, timeout)))
        self.tools.bind("engineer.git.diff_summary", self._record("engineer.git.diff_summary", lambda _a: _command(["git", "diff", "--stat"], root, timeout)))
        self.tools.bind("engineer.repo.inventory", self._record("engineer.repo.inventory", lambda a: repository_inventory(root, min(max(int(a.get("limit", 5000)), 100), 10000))))
        self.tools.bind("engineer.repo.read_file", self._record("engineer.repo.read_file", self._read_file))
        self.tools.bind("engineer.tests.run_pytest", self._record("engineer.tests.run_pytest", self._run_pytest))
    def _read_file(self, args: Mapping[str, Any]):
        path = resolve_repository_file(self.root, args.get("path"))
        return {"path": path.relative_to(self.root).as_posix(),
                "content": redact_sensitive_text(path.read_text(encoding="utf-8", errors="replace")),
                "truncated": path.stat().st_size > 12000}

    def _run_pytest(self, args: Mapping[str, Any]):
        targets = validate_test_targets(self.root, args.get("paths"))
        argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--disable-warnings", "--maxfail=1", *targets]
        return _command(argv, self.root, self.timeout)

    def _observe(self, _run: Any, _context: Any) -> Mapping[str, Any]:
        return {"recent_tool_observations": self.observations[-8:]}

    def _plan(self, context: Any) -> tuple[AIToolCall, ...]:
        if self.service is None:
            from .service import AIKernelService
            self.service = AIKernelService()
        available = [{"tool_id": x.tool_id, "description": x.description} for x in self.tools.specs()]
        prompt = (
            "Bạn là Chief Engineer của MathTeacher AI. Chỉ dùng tool trong allow-list. "
            "Không đề xuất shell command, sửa/xóa tệp, commit/push/merge/deploy hoặc đọc khóa bí mật. "
            "Trả về JSON thuần theo schema {tool_calls:[{tool_id,arguments}]}; "
            "khi đủ bằng chứng trả tool_calls rỗng.\n"
            f"Mục tiêu: {context.objective}\nChu kỳ: {context.cycle}\n"
            f"Allow-list: {json.dumps(available, ensure_ascii=False)}\n"
            f"Kết quả: {json.dumps(self.observations[-8:], ensure_ascii=False)}"
        )
        response = self.service.run(task_id=f"{context.task_id}.planner.{context.cycle}",
            prompt=prompt, capabilities=("coding", "reasoning", "general"),
            owner=AIOwnership.SYSTEM, action=AIActionClass.ADVISORY,
            metadata={"interface": "chief_engineer_agent", "mutating": "false"},
            skill_id=self.SKILL_ID)
        return parse_tool_plan(getattr(response, "text", response), self.max_steps)

    def run(self, objective: str, *, task_id: str | None = None):
        objective = str(objective or "").strip()
        if not objective or len(objective) > 2000:
            raise ValueError("Mục tiêu phải có từ 1 đến 2000 ký tự.")
        self.observations.clear()
        def planner_provider(context):
            calls = self._plan(context)
            if calls:
                self.observations.append({"cycle": context.cycle, "planned_tools": [x.tool_id for x in calls]})
            return calls
        return self.orchestrator.run(task_id=task_id or "chief-engineer-" + uuid4().hex[:12],
            skill_id=self.SKILL_ID, owner=AIOwnership.SYSTEM, objective=objective,
            planner_provider=planner_provider, max_cycles=self.max_cycles)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MathTeacher AI Chief Engineer Agent V1")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--max-cycles", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args(argv)
    try:
        run = ChiefEngineerAgent(repo_root=args.repo_root, max_cycles=args.max_cycles, timeout=args.timeout).run(args.objective)
        print(json.dumps({"run_id": run.run_id, "status": run.status.value,
            "cycles": run.cycle_count, "stop_reason": run.stop_reason,
            "approval_ids": list(run.approval_ids)}, ensure_ascii=False, indent=2))
        return 0 if run.status.value == "completed" else 2
    except Exception as exc:
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__,
            "message": redact_sensitive_text(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
