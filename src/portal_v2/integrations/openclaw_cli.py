"""Small, testable adapter for the supported OpenClaw CLI surface.

The adapter deliberately passes an argv list to ``subprocess`` and sends the
message through a temporary UTF-8 file.  User text is therefore never parsed
as a shell command.  Authentication remains owned by the local OpenClaw
installation; MathTeacher-AI neither reads nor persists the Gateway token.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Mapping, Sequence


class OpenClawError(RuntimeError):
    """A safe, user-presentable OpenClaw integration failure."""


@dataclass(frozen=True)
class OpenClawGatewayStatus:
    available: bool
    message: str


@dataclass(frozen=True)
class OpenClawTurnResult:
    text: str
    status: str
    session_id: str = ""
    run_id: str = ""


Runner = Callable[..., subprocess.CompletedProcess[str]]


def _json_object(stdout: str) -> Mapping[str, Any]:
    try:
        value = json.loads(stdout or "{}")
    except json.JSONDecodeError as error:
        raise OpenClawError(
            "OpenClaw trả về dữ liệu không đúng định dạng JSON."
        ) from error
    if not isinstance(value, Mapping):
        raise OpenClawError("OpenClaw không trả về một kết quả hợp lệ.")
    return value


def _first_text(payload: Mapping[str, Any]) -> str:
    final = str(payload.get("final", "") or "").strip()
    if final:
        return final

    candidates: list[Any] = []
    candidates.extend(payload.get("payloads", []) or [])
    result = payload.get("result")
    if isinstance(result, Mapping):
        candidates.extend(result.get("payloads", []) or [])
        candidates.append(result)
    meta = payload.get("meta")
    if isinstance(meta, Mapping):
        candidates.extend(meta.get("payloads", []) or [])

    for item in candidates:
        if isinstance(item, Mapping):
            text = str(item.get("text", "") or "").strip()
            if text:
                return text
    return ""


class OpenClawCLI:
    """Invoke Gateway-backed OpenClaw turns without shell interpolation."""

    def __init__(
        self,
        *,
        executable: str | None = None,
        runner: Runner = subprocess.run,
    ) -> None:
        self._executable = executable or shutil.which("openclaw") or ""
        self._runner = runner

    @property
    def installed(self) -> bool:
        return bool(self._executable)

    def gateway_status(self, *, timeout_seconds: int = 12) -> OpenClawGatewayStatus:
        if not self.installed:
            return OpenClawGatewayStatus(
                False,
                "Chưa tìm thấy OpenClaw trong PATH của máy đang chạy ứng dụng.",
            )
        try:
            completed = self._run(
                [self._executable, "gateway", "status", "--json"],
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired):
            return OpenClawGatewayStatus(
                False,
                "Không nhận được phản hồi từ OpenClaw Gateway.",
            )
        if completed.returncode != 0:
            return OpenClawGatewayStatus(
                False,
                "Gateway chưa hoạt động. Hãy chạy openclaw gateway start rồi kiểm tra lại.",
            )
        return OpenClawGatewayStatus(True, "OpenClaw Gateway đang hoạt động.")

    def send_turn(
        self,
        *,
        message: str,
        agent_id: str,
        session_key: str,
        timeout_seconds: int = 600,
    ) -> OpenClawTurnResult:
        clean_message = message.strip()
        clean_agent = agent_id.strip()
        clean_session = session_key.strip()
        if not clean_message:
            raise ValueError("Nội dung gửi OpenClaw không được để trống.")
        if not clean_agent or not clean_session:
            raise ValueError("Agent và khóa phiên OpenClaw phải hợp lệ.")
        if not self.installed:
            raise OpenClawError(
                "Chưa tìm thấy OpenClaw trong PATH của máy đang chạy ứng dụng."
            )

        message_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".txt",
                prefix="mathteacher-openclaw-",
                delete=False,
            ) as handle:
                handle.write(clean_message)
                message_path = handle.name

            argv = [
                self._executable,
                "agent",
                "--agent",
                clean_agent,
                "--session-key",
                clean_session,
                "--message-file",
                message_path,
                "--timeout",
                str(timeout_seconds),
                "--json",
            ]
            try:
                completed = self._run(argv, timeout=timeout_seconds + 15)
            except subprocess.TimeoutExpired as error:
                raise OpenClawError(
                    "OpenClaw xử lý quá thời gian cho phép. Hãy kiểm tra phiên trước khi gửi lại để tránh chạy trùng nhiệm vụ."
                ) from error
            except OSError as error:
                raise OpenClawError("Không thể khởi chạy lệnh OpenClaw.") from error
        finally:
            if message_path:
                Path(message_path).unlink(missing_ok=True)

        payload = _json_object(completed.stdout)
        status = str(payload.get("status", "") or "").strip().lower()
        if completed.returncode != 0 or payload.get("ok") is False:
            error = payload.get("error")
            detail = ""
            if isinstance(error, Mapping):
                detail = str(error.get("message", "") or "").strip()
            raise OpenClawError(detail or "OpenClaw chưa hoàn thành được yêu cầu.")

        text = _first_text(payload)
        if not text:
            raise OpenClawError("OpenClaw đã hoàn tất nhưng không trả về nội dung.")
        return OpenClawTurnResult(
            text=text,
            status=status or "ok",
            session_id=str(payload.get("sessionId", "") or ""),
            run_id=str(payload.get("runId", "") or ""),
        )

    def _run(
        self,
        argv: Sequence[str],
        *,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        return self._runner(
            list(argv),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=timeout,
        )
