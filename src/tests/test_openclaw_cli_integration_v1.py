from __future__ import annotations

import json
import subprocess

import pytest

from portal_v2.integrations.openclaw_cli import OpenClawCLI, OpenClawError


def completed(*, stdout: str, returncode: int = 0):
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")


def test_gateway_status_uses_supported_cli_without_shell() -> None:
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return completed(stdout='{"ok":true}')

    client = OpenClawCLI(executable="openclaw", runner=runner)
    status = client.gateway_status()

    assert status.available is True
    assert calls[0][0] == ["openclaw", "gateway", "status", "--json"]
    assert calls[0][1]["shell"] is False


def test_send_turn_uses_message_file_and_extracts_final_text() -> None:
    observed = {}

    def runner(argv, **kwargs):
        observed["argv"] = argv
        observed["message"] = open(
            argv[argv.index("--message-file") + 1], encoding="utf-8"
        ).read()
        observed["shell"] = kwargs["shell"]
        return completed(stdout=json.dumps({
            "ok": True,
            "status": "ok",
            "final": "Đã kiểm tra xong.",
            "sessionId": "session-1",
        }))

    client = OpenClawCLI(executable="openclaw", runner=runner)
    result = client.send_turn(
        message='Kiểm tra; $(không chạy shell)',
        agent_id="mathteacher-engineer",
        session_key="mathteacher-ui-test",
    )

    assert result.text == "Đã kiểm tra xong."
    assert observed["message"] == 'Kiểm tra; $(không chạy shell)'
    assert observed["shell"] is False
    assert "--agent" in observed["argv"]
    assert "mathteacher-engineer" in observed["argv"]


def test_send_turn_preserves_gateway_failure_message() -> None:
    def runner(argv, **kwargs):
        return completed(
            returncode=1,
            stdout=json.dumps({
                "ok": False,
                "status": "error",
                "error": {"message": "Gateway unavailable"},
            }),
        )

    client = OpenClawCLI(executable="openclaw", runner=runner)
    with pytest.raises(OpenClawError, match="Gateway unavailable"):
        client.send_turn(
            message="Kiểm tra",
            agent_id="mathteacher-engineer",
            session_key="mathteacher-ui-test",
        )


def test_empty_message_is_rejected_before_process_start() -> None:
    client = OpenClawCLI(
        executable="openclaw",
        runner=lambda *args, **kwargs: pytest.fail("runner must not be called"),
    )
    with pytest.raises(ValueError, match="không được để trống"):
        client.send_turn(
            message="  ",
            agent_id="mathteacher-engineer",
            session_key="mathteacher-ui-test",
        )
