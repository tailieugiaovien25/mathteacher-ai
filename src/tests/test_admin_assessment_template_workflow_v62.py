"""Contract tests for the governed ADMIN template workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from portal_v2.ui.admin_assessment_template_workflow_streamlit import (
    DEFAULT_TEMPLATE_CODE,
    _load_state,
)


ROOT = Path(__file__).resolve().parents[1]
UI_FILE = (
    ROOT
    / "portal_v2"
    / "ui"
    / "admin_assessment_template_workflow_streamlit.py"
)
NAVIGATION_FILE = ROOT / "portal_v2" / "ui" / "admin_navigation.py"
SHELL_FILE = ROOT / "portal_v2" / "ui" / "admin_shell.py"


@dataclass
class _Response:
    data: list[dict[str, Any]]


class _Query:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.table_name = ""
        self.filters: list[tuple[str, object]] = []

    def table(self, table_name: str) -> "_Query":
        self.table_name = table_name
        return self

    def select(self, _columns: str) -> "_Query":
        return self

    def eq(self, column: str, value: object) -> "_Query":
        self.filters.append((column, value))
        return self

    def limit(self, _count: int) -> "_Query":
        return self

    def execute(self) -> _Response:
        return _Response(self.rows)


def test_load_state_returns_none_before_bootstrap() -> None:
    assert _load_state(client=_Query([])) is None


def test_load_state_uses_latest_template_version() -> None:
    query = _Query(
        [
            {
                "template_set_id": "set-1",
                "template_name": "Bộ mẫu linh hoạt",
                "lifecycle_status": "DRAFT",
                "current_version_number": 0,
                "assessment_document_template_versions": [
                    {
                        "template_version_id": "version-1",
                        "version_number": 1,
                        "review_status": "DRAFT",
                    },
                    {
                        "template_version_id": "version-2",
                        "version_number": 2,
                        "review_status": "PENDING_REVIEW",
                    },
                ],
            }
        ]
    )

    state = _load_state(client=query)

    assert state is not None
    assert state.template_version_id == "version-2"
    assert state.version_number == 2
    assert state.review_status == "PENDING_REVIEW"
    assert query.table_name == "assessment_document_template_sets"
    assert query.filters == [("template_code", DEFAULT_TEMPLATE_CODE)]


def test_page_exposes_four_explicit_human_actions() -> None:
    text = UI_FILE.read_text(encoding="utf-8")

    for label in (
        "1. Tạo bản nháp bộ mẫu",
        "2. Gửi bộ mẫu để duyệt",
        "3. Phê duyệt bộ mẫu",
        "4. Kích hoạt bộ mẫu",
    ):
        assert label in text

    assert "Mỗi nút chỉ thực hiện một bước" in text
    assert "không tự phê duyệt" in text


def test_page_calls_only_governed_template_rpcs() -> None:
    text = UI_FILE.read_text(encoding="utf-8")

    for function_name in (
        "create_default_assessment_document_template_draft",
        "submit_assessment_document_template_for_review",
        "review_assessment_document_template",
        "activate_assessment_document_template_version",
    ):
        assert function_name in text

    for forbidden in (
        ".insert(",
        ".update(",
        ".delete(",
        "service_role",
    ):
        assert forbidden not in text


def test_admin_navigation_and_shell_are_wired() -> None:
    navigation = NAVIGATION_FILE.read_text(encoding="utf-8")
    shell = SHELL_FILE.read_text(encoding="utf-8")

    assert "ADMIN_PAGE_ASSESSMENT_TEMPLATES" in navigation
    assert '"Bộ mẫu đề kiểm tra"' in navigation
    assert "ADMIN_PAGE_ASSESSMENT_TEMPLATES" in shell
    assert "render_admin_assessment_template_workflow" in shell
