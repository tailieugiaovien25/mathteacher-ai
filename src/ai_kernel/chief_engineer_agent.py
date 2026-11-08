"""MathTeacher AI Chief Engineer Agent V2: bounded inspection and approved patching."""
from __future__ import annotations
import argparse
import ast
import difflib
import hashlib
import hmac
import getpass
import json
import os
import re
import subprocess
import tempfile
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from .agent_planner import SafeAgentPlanner
from .agent_runtime import AIToolCall, AIToolRegistry, AIToolSpec, JSONAgentRunStore, SafeAgentRuntime
from .approval_queue import ApprovalQueue, JSONApprovalQueueStore
from .autonomous_orchestrator import AutonomousOrchestrator, JSONAutonomousRunStore
from .contracts import AIActionClass, AIOwnership
from .skills import AISkillDomain, AISkillSpec, default_ai_skills

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


def _safe_child_environment() -> dict[str, str]:
    """Pass only runtime necessities to subprocesses, never inherited credentials."""
    allowed = (
        "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
        "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE",
        "LOCALAPPDATA", "APPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)",
        "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "LANG", "LC_ALL",
    )
    result = {name: os.environ[name] for name in allowed if os.environ.get(name)}
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    return result


def _command(argv: list[str], root: Path, timeout: int) -> dict[str, Any]:
    try:
        result = subprocess.run(
            argv, cwd=str(root), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            timeout=timeout, shell=False,
            env=_safe_child_environment(), check=False,
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
        source = "\n".join(lines).strip()
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


def chief_engineer_tool_specs(*, include_tests: bool = True) -> tuple[AIToolSpec, ...]:
    safe = frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY})
    specs = (
        AIToolSpec("engineer.git.status", "Git status", "Đọc trạng thái Git.", safe, ("coding", "repository")),
        AIToolSpec("engineer.git.diff_summary", "Git diff summary", "Đọc thống kê thay đổi.", safe, ("coding", "repository")),
        AIToolSpec("engineer.repo.inventory", "Repository inventory", "Thống kê cấu trúc tệp; loại trừ vùng bí mật.", safe, ("coding", "repository")),
        AIToolSpec("engineer.repo.read_file", "Read source file", "Đọc mã nguồn/tài liệu trong allow-list.", safe, ("coding", "repository")),
        AIToolSpec("engineer.tests.run_pytest", "Run selected tests", "Chạy tối đa 5 test file cụ thể.", safe, ("coding", "testing")),
    )
    return tuple(spec for spec in specs if include_tests or spec.tool_id != "engineer.tests.run_pytest")


PATCH_MAX_FILES = 5
PATCH_MAX_BYTES = 262144
PATCH_APPLY_TOOL = "engineer.patch.apply"
PATCH_SKILL_ID = "system_admin.maintenance"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_write_bytes(path: Path, value: bytes, *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="mathteacher-safe-write-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    _atomic_write_bytes(path, encoded)


def _patch_manifest_digest(manifest: Mapping[str, Any]) -> str:
    stable = {
        "patch_id": manifest["patch_id"],
        "task_id": manifest["task_id"],
        "rationale": manifest["rationale"],
        "changes": manifest["changes"],
    }
    encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


def _reject_secret_payload(content: str) -> None:
    patterns = (
        r'''(?im)^\s*[A-Za-z0-9_]*(?:API[_-]?KEY|CLIENT[_-]?SECRET|PASSWORD|ACCESS[_-]?TOKEN|REFRESH[_-]?TOKEN)\s*[:=]\s*['"]?[^'"\s#]{8,}''',
        r"\b(?:ghp|gho|ghs|ghu|ghr)_[A-Za-z0-9_]{20,}\b",
        r"\bsk-[A-Za-z0-9_-]{20,}\b",
        r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{20,}",
    )
    if any(re.search(pattern, content) for pattern in patterns):
        raise ValueError("Bản vá có dấu hiệu chứa khóa bí mật; đã từ chối lưu đề xuất.")


def _resolve_patch_target(root: Path, raw_path: object) -> Path:
    raw = str(raw_path or "").strip()
    if not raw or chr(0) in raw or "\\" in raw:
        raise ValueError("Đường dẫn bản vá không hợp lệ.")
    candidate = Path(raw)
    if candidate.is_absolute() or not raw.startswith("src/") or candidate.suffix.casefold() != ".py":
        raise ValueError("Bản vá V2 chỉ được nhắm tới tệp Python hiện có bên trong src/.")
    root = root.resolve()
    cursor = root
    for part in candidate.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("Không cho phép bản vá đi qua symbolic link.")
    resolved = cursor.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Đường dẫn bản vá vượt ra ngoài repository.") from exc
    if _sensitive(relative) or not resolved.is_file():
        raise ValueError("Tệp bản vá không tồn tại hoặc thuộc vùng bị bảo vệ.")
    if resolved.stat().st_size > PATCH_MAX_BYTES:
        raise ValueError("Tệp nguồn hiện tại vượt giới hạn bản vá.")
    return resolved


def _validate_patch_changes(root: Path, changes: object) -> list[dict[str, str]]:
    if not isinstance(changes, list) or not changes or len(changes) > PATCH_MAX_FILES:
        raise ValueError(f"Một bản vá cần từ 1 đến {PATCH_MAX_FILES} tệp.")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for change in changes:
        if not isinstance(change, dict) or set(change) != {"path", "content", "expected_sha256"}:
            raise ValueError("Mỗi thay đổi phải có đúng path, content và expected_sha256.")
        path = _resolve_patch_target(root, change["path"])
        relative = path.relative_to(root).as_posix()
        if relative in seen:
            raise ValueError("Bản vá chứa đường dẫn trùng lặp.")
        seen.add(relative)
        content = change["content"]
        expected = str(change["expected_sha256"] or "").strip().lower()
        if not isinstance(content, str) or not content or len(content.encode("utf-8")) > PATCH_MAX_BYTES:
            raise ValueError("Nội dung mới rỗng hoặc vượt giới hạn kích thước.")
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("expected_sha256 phải là SHA-256 hợp lệ.")
        current = path.read_bytes()
        if _sha256_bytes(current) != expected:
            raise ValueError(f"Tệp nguồn đã thay đổi kể từ lúc phân tích: {relative}")
        _reject_secret_payload(content)
        try:
            ast.parse(content, filename=relative)
        except SyntaxError as exc:
            raise ValueError(f"Bản vá Python không hợp lệ tại {relative}: dòng {exc.lineno}.") from exc
        normalized.append({"path": relative, "expected_sha256": expected, "content": content})
    return normalized


class ChiefEngineerAgent:
    """Model-planned repo observer built on SafeAgentPlanner/Runtime/Orchestrator."""
    SKILL_ID = "system_admin.observer"

    def __init__(self, *, repo_root: str | os.PathLike[str], service: Any | None = None,
                 state_dir: str | os.PathLike[str] | None = None, timeout: int = 90,
                 max_cycles: int = 4, max_steps: int = 6, allow_tests: bool = True):
        self.root = Path(repo_root).expanduser().resolve()
        if not self.root.is_dir() or not (self.root / ".git").exists():
            raise ValueError("repo_root phải là Git repository.")
        self.timeout = min(max(int(timeout), 5), 300)
        self.max_cycles = min(max(int(max_cycles), 1), 8)
        self.max_steps = min(max(int(max_steps), 1), 12)
        self.allow_tests = bool(allow_tests)
        self.state_dir = Path(state_dir).resolve() if state_dir else self.root / ".mathteacher_ai" / "chief_engineer"
        if self.state_dir == self.root or (self.root in self.state_dir.parents and self.state_dir != self.root / ".mathteacher_ai" / "chief_engineer"):
            raise ValueError("state_dir trong repo chỉ được phép là .mathteacher_ai/chief_engineer.")
        self.service = service
        self.observations: list[dict[str, Any]] = []
        self.approvals = ApprovalQueue(JSONApprovalQueueStore(self.state_dir / "approvals.json"))
        maintenance_skill = AISkillSpec(
            skill_id=PATCH_SKILL_ID,
            label="Chief Engineer code maintenance",
            domain=AISkillDomain.SYSTEM_ADMIN,
            capabilities=("coding", "repository", "testing"),
            allowed_actions=frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY, AIActionClass.MUTATING}),
            description="Áp dụng bản vá mã nguồn sau sao lưu và ADMIN phê duyệt.",
        )
        skills = (*default_ai_skills(), maintenance_skill)
        patch_tool = AIToolSpec(
            tool_id=PATCH_APPLY_TOOL,
            label="Apply approved source patch",
            description="Áp dụng bản vá đã duyệt; tạo backup trước khi ghi tệp.",
            allowed_actions=frozenset({AIActionClass.MUTATING}),
            capabilities=("coding", "repository"),
            requires_admin_approval=True,
        )
        self.tools = AIToolRegistry((*chief_engineer_tool_specs(), patch_tool))
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
        if self.allow_tests:
            self.tools.bind("engineer.tests.run_pytest", self._record("engineer.tests.run_pytest", self._run_pytest))
        self.tools.bind(PATCH_APPLY_TOOL, self._apply_patch_tool)
    def _read_file(self, args: Mapping[str, Any]):
        path = resolve_repository_file(self.root, args.get("path"))
        return {"path": path.relative_to(self.root).as_posix(),
                "content": redact_sensitive_text(path.read_text(encoding="utf-8", errors="replace")),
                "truncated": path.stat().st_size > 12000}

    def _run_pytest(self, args: Mapping[str, Any]):
        targets = validate_test_targets(self.root, args.get("paths"))
        argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--disable-warnings", "--maxfail=1", *targets]
        return _command(argv, self.root, self.timeout)

    def _patch_manifest_path(self, patch_id: object) -> Path:
        identifier = str(patch_id or "").strip()
        if not re.fullmatch(r"[a-f0-9]{32}", identifier):
            raise ValueError("Mã bản vá không hợp lệ.")
        return self.state_dir / "patches" / (identifier + ".json")

    def _load_patch_manifest(self, patch_id: object) -> dict[str, Any]:
        path = self._patch_manifest_path(patch_id)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError("Không tìm thấy đề xuất bản vá.") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Không đọc được hồ sơ bản vá; từ chối áp dụng.") from exc
        if not isinstance(payload, dict) or payload.get("patch_id") != str(patch_id):
            raise ValueError("Hồ sơ bản vá không hợp lệ.")
        if _patch_manifest_digest(payload) != payload.get("proposal_sha256"):
            raise ValueError("Nội dung đề xuất đã thay đổi sau khi phê duyệt; từ chối áp dụng.")
        return payload

    def draft_patch(self, paths, *, rationale):
        """Generate a bounded source patch proposal using the configured AI Kernel."""
        reason = str(rationale or "").strip()
        if not reason or len(reason) > 1200:
            raise ValueError("Lý do bản vá phải từ 1 đến 1200 ký tự.")
        if not isinstance(paths, (list, tuple)) or not paths or len(paths) > 3:
            raise ValueError("Mỗi đề xuất AI chỉ nhận từ 1 đến 3 tệp Python.")
        sources = []
        allowed = set()
        total = 0
        for raw_path in paths:
            source_path = _resolve_patch_target(self.root, raw_path)
            relative = source_path.relative_to(self.root).as_posix()
            if relative in allowed:
                raise ValueError("Danh sách tệp bị trùng.")
            allowed.add(relative)
            content = source_path.read_text(encoding="utf-8")
            _reject_secret_payload(content)
            total += len(content)
            if total > 24000:
                raise ValueError("Tổng mã nguồn gửi tới AI vượt 24.000 ký tự.")
            sources.append({
                "path": relative,
                "expected_sha256": _sha256_bytes(source_path.read_bytes()),
                "content": content,
            })
        if self.service is None:
            from .service import AIKernelService
            self.service = AIKernelService()
        prompt = (
            "Bạn là kỹ sư phần mềm MathTeacher AI. Tạo bản vá tối thiểu theo mục tiêu. "
            "Chỉ sửa đúng các tệp được cung cấp; không thêm, xóa, đổi tên tệp; không dùng shell; "
            "không sửa khóa bí mật; giữ nguyên hành vi ngoài phạm vi. "
            "Trả JSON thuần có khóa changes là danh sách các object chỉ gồm path và content. "
            "content phải là TOÀN BỘ mã Python mới của tệp. Không dùng Markdown fence. "
            "Nếu không cần sửa, trả danh sách changes rỗng.\n"
            f"Mục tiêu: {reason}\n"
            f"Mã nguồn: {json.dumps(sources, ensure_ascii=False)}"
        )
        response = self.service.run(
            task_id="chief-engineer-draft-" + uuid4().hex[:12],
            prompt=prompt,
            capabilities=("coding", "reasoning", "general"),
            owner=AIOwnership.SYSTEM,
            action=AIActionClass.ADVISORY,
            metadata={"interface": "chief_engineer_patch_drafter", "mutating": "false"},
            skill_id=self.SKILL_ID,
        )
        raw = str(getattr(response, "text", response) or "").strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines and lines[0].lstrip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines).strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("AI không trả về JSON bản vá hợp lệ.") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("changes"), list):
            raise ValueError("Cấu trúc bản vá AI không hợp lệ.")
        proposed = payload["changes"]
        if not proposed:
            raise ValueError("AI đề xuất không cần thay đổi; không tạo approval.")
        if len(proposed) != len(sources):
            raise ValueError("AI phải trả đủ nội dung cho tất cả tệp đã chọn.")
        by_path = {}
        for row in proposed:
            if not isinstance(row, dict) or set(row) != {"path", "content"}:
                raise ValueError("Mỗi thay đổi phải có đúng path và content.")
            name = str(row["path"] or "")
            if name not in allowed or name in by_path or not isinstance(row["content"], str):
                raise ValueError("AI đề xuất đường dẫn ngoài phạm vi hoặc trùng lặp.")
            by_path[name] = row["content"]
        staged = [{
            "path": item["path"],
            "content": by_path[item["path"]],
            "expected_sha256": item["expected_sha256"],
        } for item in sources]
        result = self.prepare_patch(staged, rationale=reason)
        result["generated_by_ai"] = True
        return result

    def prepare_patch(self, changes: object, *, rationale: str) -> dict[str, Any]:
        """Store a proposed source patch and create a pending ADMIN approval.

        This method never changes repository source files.
        """
        reason = str(rationale or "").strip()
        if not reason or len(reason) > 1200:
            raise ValueError("Lý do bản vá phải từ 1 đến 1200 ký tự.")
        normalized = _validate_patch_changes(self.root, changes)
        patch_id = uuid4().hex
        task_id = "chief-engineer-patch:" + patch_id
        manifest: dict[str, Any] = {
            "patch_id": patch_id,
            "task_id": task_id,
            "rationale": redact_sensitive_text(reason),
            "changes": normalized,
            "status": "awaiting_approval",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "approval_id": "",
        }
        manifest["proposal_sha256"] = _patch_manifest_digest(manifest)
        manifest_path = self._patch_manifest_path(patch_id)
        _write_json_atomic(manifest_path, manifest)
        approval = self.approvals.create(
            task_id=task_id,
            skill_id=PATCH_SKILL_ID,
            tool_id=PATCH_APPLY_TOOL,
            arguments={"patch_id": patch_id, "proposal_sha256": manifest["proposal_sha256"]},
            requester=AIOwnership.SYSTEM,
            rationale=manifest["rationale"],
            risk_level="high",
        )
        manifest["approval_id"] = approval.approval_id
        _write_json_atomic(manifest_path, manifest)
        return {
            "patch_id": patch_id,
            "approval_id": approval.approval_id,
            "proposal_sha256": manifest["proposal_sha256"],
            "status": manifest["status"],
            "files": [item["path"] for item in normalized],
            "source_changed": False,
        }

    def _apply_patch_tool(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if set(arguments) != {"patch_id", "proposal_sha256"}:
            raise ValueError("Tham số áp dụng bản vá không hợp lệ.")
        manifest = self._load_patch_manifest(arguments.get("patch_id"))
        if manifest.get("status") != "awaiting_approval":
            raise ValueError("Bản vá không còn ở trạng thái chờ phê duyệt.")
        if arguments.get("proposal_sha256") != manifest.get("proposal_sha256"):
            raise ValueError("Mã kiểm tra bản vá không khớp.")
        approval_id = str(manifest.get("approval_id") or "")
        approval = self.approvals.get(approval_id)
        if (
            approval.tool_id != PATCH_APPLY_TOOL
            or approval.skill_id != PATCH_SKILL_ID
            or approval.arguments != dict(arguments)
            or approval.task_id != manifest.get("task_id")
        ):
            raise ValueError("Approval không khớp hồ sơ bản vá.")

        # Revalidate every source hash immediately before taking backups.
        normalized = _validate_patch_changes(self.root, manifest.get("changes"))
        patch_backup_root = self.state_dir / "backups" / str(manifest["patch_id"])
        patch_backup_root.mkdir(parents=True, exist_ok=False)
        backups: list[dict[str, str]] = []
        original_modes: dict[str, int] = {}
        originals: dict[str, bytes] = {}
        for item in normalized:
            source_path = _resolve_patch_target(self.root, item["path"])
            original = source_path.read_bytes()
            original_sha = _sha256_bytes(original)
            if original_sha != item["expected_sha256"]:
                raise ValueError(f"Tệp nguồn thay đổi khi chuẩn bị backup: {item['path']}")
            backup_path = patch_backup_root / item["path"]
            _atomic_write_bytes(backup_path, original, mode=source_path.stat().st_mode & 0o777)
            originals[item["path"]] = original
            original_modes[item["path"]] = source_path.stat().st_mode & 0o777
            backups.append({
                "path": item["path"],
                "backup_path": backup_path.relative_to(self.state_dir).as_posix(),
                "sha256": original_sha,
            })

        manifest["backups"] = backups
        manifest["status"] = "backed_up"
        manifest["backed_up_at"] = datetime.now(timezone.utc).isoformat()
        _write_json_atomic(self._patch_manifest_path(manifest["patch_id"]), manifest)

        applied: list[str] = []
        try:
            for item in normalized:
                source_path = _resolve_patch_target(self.root, item["path"])
                # Close the time-of-check/time-of-use window as far as practical.
                if _sha256_bytes(source_path.read_bytes()) != item["expected_sha256"]:
                    raise ValueError(f"Tệp nguồn thay đổi trước khi ghi: {item['path']}")
                _atomic_write_bytes(
                    source_path,
                    item["content"].encode("utf-8"),
                    mode=original_modes[item["path"]],
                )
                applied.append(item["path"])
            manifest["status"] = "applied"
            manifest["applied_at"] = datetime.now(timezone.utc).isoformat()
            manifest["applied_paths"] = list(applied)
            # Persist the applied marker inside the transaction scope. If this
            # write fails after source replacement, restore files from backups.
            _write_json_atomic(self._patch_manifest_path(manifest["patch_id"]), manifest)
        except Exception as exc:
            rollback_errors: list[str] = []
            for relative in reversed(applied):
                try:
                    source_path = _resolve_patch_target(self.root, relative)
                    _atomic_write_bytes(source_path, originals[relative], mode=original_modes[relative])
                except Exception as rollback_exc:
                    rollback_errors.append(relative + ": " + type(rollback_exc).__name__)
            manifest["status"] = "rollback_failed" if rollback_errors else "rolled_back"
            manifest["failure"] = type(exc).__name__
            manifest["rollback_errors"] = rollback_errors
            try:
                _write_json_atomic(self._patch_manifest_path(manifest["patch_id"]), manifest)
            except Exception as manifest_exc:
                rollback_errors.append("manifest: " + type(manifest_exc).__name__)
            if rollback_errors:
                raise RuntimeError("Áp dụng bản vá lỗi hoặc trạng thái rollback chưa ghi được; cần kiểm tra backup.") from exc
            raise RuntimeError("Áp dụng bản vá lỗi; các tệp đã ghi được khôi phục từ backup.") from exc
        return {
            "patch_id": manifest["patch_id"],
            "status": "applied",
            "files": applied,
            "backups": backups,
        }

    def patch_preview(self, patch_id: str) -> str:
        """Render a bounded unified diff for explicit human review before approval."""
        manifest = self._load_patch_manifest(patch_id)
        if manifest.get("status") != "awaiting_approval":
            raise ValueError("Bản vá không còn ở trạng thái chờ phê duyệt.")
        chunks: list[str] = []
        for item in manifest.get("changes", []):
            source_path = _resolve_patch_target(self.root, item["path"])
            original = source_path.read_text(encoding="utf-8")
            if _sha256_bytes(source_path.read_bytes()) != item["expected_sha256"]:
                raise ValueError("Tệp nguồn đã thay đổi; cần tạo đề xuất mới.")
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                item["content"].splitlines(keepends=True),
                fromfile="a/" + item["path"],
                tofile="b/" + item["path"],
            )
            chunks.extend(diff)
        preview = redact_sensitive_text("".join(chunks))
        return preview[:30000] or "(Bản vá không tạo ra khác biệt.)"

    def approve_and_apply_patch(
        self,
        approval_id: str,
        *,
        admin_actor: str,
        admin_token: str,
        confirmation: str,
    ):
        """Approve and consume a pending patch exactly once after explicit confirmation."""
        expected_confirmation = "APPLY PATCH " + str(approval_id or "").strip()
        if confirmation != expected_confirmation:
            raise ValueError("Xác nhận không khớp; bản vá chưa được phê duyệt hoặc áp dụng.")
        configured_token = os.getenv("MATH_TEACHER_AI_CHIEF_ENGINEER_ADMIN_TOKEN", "")
        if len(configured_token) < 32 or not hmac.compare_digest(str(admin_token or ""), configured_token):
            raise PermissionError("Không xác thực được ADMIN token cục bộ; chưa có thay đổi mã nguồn.")
        if not str(admin_actor or "").strip():
            raise ValueError("ADMIN actor là bắt buộc.")
        approval = self.approvals.get(approval_id)
        if approval.tool_id != PATCH_APPLY_TOOL or approval.skill_id != PATCH_SKILL_ID:
            raise ValueError("Approval này không phải yêu cầu áp dụng bản vá.")
        if approval.status.value not in {"pending", "approved"}:
            raise ValueError("Approval không còn ở trạng thái có thể thực thi.")
        manifest = self._load_patch_manifest(approval.arguments.get("patch_id"))
        if (
            manifest.get("approval_id") != approval_id
            or manifest.get("task_id") != approval.task_id
            or manifest.get("proposal_sha256") != approval.arguments.get("proposal_sha256")
        ):
            raise ValueError("Approval không khớp đề xuất bản vá.")
        approved = approval
        if approval.status.value == "pending":
            approved = self.approvals.approve(
                approval_id,
                admin_actor=admin_actor,
                actor_owner=AIOwnership.ADMIN,
            )
        # An APPROVED but unclaimed request can be resumed after an interrupted
        # CLI session. EXECUTING requests are never replayed automatically.
        run = self.runtime.run(
            task_id=approved.task_id,
            skill_id=PATCH_SKILL_ID,
            owner=AIOwnership.SYSTEM,
            plan=(AIToolCall(PATCH_APPLY_TOOL, dict(approved.arguments)),),
            approval_id=approved.approval_id,
            approval_token=approved.execution_token,
            max_steps=1,
        )
        if run.status.value != "completed":
            raise RuntimeError("Agent không áp dụng được bản vá; trạng thái: " + run.status.value)
        return run

    def patch_status(self, patch_id: str) -> dict[str, Any]:
        manifest = self._load_patch_manifest(patch_id)
        return {
            "patch_id": manifest["patch_id"],
            "status": manifest.get("status", "unknown"),
            "files": [item["path"] for item in manifest.get("changes", [])],
            "approval_id": manifest.get("approval_id", ""),
            "backups": manifest.get("backups", []),
        }

    def _observe(self, _run: Any, _context: Any) -> Mapping[str, Any]:
        return {"recent_tool_observations": self.observations[-8:]}

    def _plan(self, context: Any) -> tuple[AIToolCall, ...]:
        if self.service is None:
            from .service import AIKernelService
            self.service = AIKernelService()
        read_actions = {AIActionClass.READ_ONLY, AIActionClass.ADVISORY}
        available = [
            {"tool_id": spec.tool_id, "description": spec.description}
            for spec in self.tools.specs()
            if spec.allowed_actions.issubset(read_actions)
        ]
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
    parser = argparse.ArgumentParser(description="MathTeacher AI Chief Engineer Agent V2")
    parser.add_argument("--repo-root", required=True)
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--objective", help="Chạy kiểm tra repository bằng AI Planner.")
    command.add_argument("--prepare-patch-file", help="Đọc JSON patch proposal và tạo yêu cầu ADMIN approval.")
    command.add_argument("--draft-patch-for", help="Danh sách đường dẫn src/*.py, phân tách bằng dấu phẩy; AI sẽ tạo bản vá nháp.")
    command.add_argument("--approve-patch-id", help="Phê duyệt và áp dụng patch ID sau khi xác nhận tương tác.")
    parser.add_argument("--rationale", default="", help="Mục tiêu sửa lỗi khi dùng --draft-patch-for.")
    parser.add_argument("--admin-actor", default="", help="Mã định danh ADMIN trong nhật ký phê duyệt.")
    parser.add_argument("--max-cycles", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--no-tests", action="store_true", help="Không đăng ký hoặc chạy công cụ pytest.")
    args = parser.parse_args(argv)
    try:
        agent = ChiefEngineerAgent(
            repo_root=args.repo_root,
            max_cycles=args.max_cycles,
            timeout=args.timeout,
            allow_tests=not args.no_tests,
        )
        if args.prepare_patch_file:
            proposal_path = Path(args.prepare_patch_file).expanduser().resolve()
            payload = json.loads(proposal_path.read_text(encoding="utf-8-sig"))
            if not isinstance(payload, dict) or set(payload) != {"rationale", "changes"}:
                raise ValueError("JSON patch proposal phải có đúng rationale và changes.")
            result = agent.prepare_patch(payload["changes"], rationale=payload["rationale"])
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.draft_patch_for:
            paths = [item.strip() for item in args.draft_patch_for.split(",") if item.strip()]
            result = agent.draft_patch(paths, rationale=args.rationale)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print(agent.patch_preview(result["patch_id"]))
            return 0
        if args.approve_patch_id:
            if not args.admin_actor.strip():
                raise ValueError("--admin-actor là bắt buộc khi áp dụng patch.")
            print(agent.patch_preview(args.approve_patch_id))
            expected = "APPLY PATCH " + args.approve_patch_id.strip()
            confirmation = input("Đã xem diff. Để phê duyệt và áp dụng, nhập chính xác: " + expected + "\n> ")
            admin_token = getpass.getpass("ADMIN token (không hiển thị): ")
            run = agent.approve_and_apply_patch(
                args.approve_patch_id,
                admin_actor=args.admin_actor,
                admin_token=admin_token,
                confirmation=confirmation,
            )
            print(json.dumps({
                "run_id": run.run_id,
                "status": run.status.value,
                "approval_id": args.approve_patch_id,
                "patch": agent.patch_status(agent.approvals.get(args.approve_patch_id).arguments["patch_id"]),
                "execution_token": "[NOT DISPLAYED]",
            }, ensure_ascii=False, indent=2))
            return 0
        run = agent.run(args.objective)
        print(json.dumps({
            "run_id": run.run_id,
            "status": run.status.value,
            "cycles": run.cycle_count,
            "stop_reason": run.stop_reason,
            "approval_ids": list(run.approval_ids),
        }, ensure_ascii=False, indent=2))
        return 0 if run.status.value == "completed" else 2
    except Exception as exc:
        print(json.dumps({
            "status": "failed",
            "error_type": type(exc).__name__,
            "message": redact_sensitive_text(exc),
        }, ensure_ascii=False, indent=2))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
