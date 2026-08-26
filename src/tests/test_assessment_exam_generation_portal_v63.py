"""Portal contracts for governed assessment draft generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from portal_v2.ui.assessment_exam_generation_streamlit import (
    SupabaseAssessmentGenerationCatalog,
)


USER_ID = "11111111-1111-4111-8111-111111111111"
ROOT = Path(__file__).resolve().parents[1]
UI_FILE = ROOT / "portal_v2" / "ui" / "assessment_exam_generation_streamlit.py"
APP_FILE = ROOT.parent / "scripts" / "teacher_portal" / "app.py"


@dataclass
class _Response:
    data: object


class _NotFilter:
    def __init__(self, query: "_Query") -> None:
        self.query = query

    def is_(self, column: str, value: object) -> "_Query":
        self.query.operations.append(("not_is", column, value))
        return self.query


class _Query:
    def __init__(self, rows: object) -> None:
        self.rows = rows
        self.operations: list[tuple[object, ...]] = []

    @property
    def not_(self) -> _NotFilter:
        return _NotFilter(self)

    def select(self, value: str) -> "_Query":
        self.operations.append(("select", value))
        return self

    def eq(self, column: str, value: object) -> "_Query":
        self.operations.append(("eq", column, value))
        return self

    def order(self, column: str, *, desc: bool = False) -> "_Query":
        self.operations.append(("order", column, desc))
        return self

    def execute(self) -> _Response:
        return _Response(self.rows)


class _Client:
    def __init__(self, rows: object) -> None:
        self.query = _Query(rows)
        self.table_name = ""

    def table(self, name: str) -> _Query:
        self.table_name = name
        return self.query


def test_catalog_lists_only_governed_blueprints() -> None:
    client = _Client(
        [
            {
                "profile_code": "TOAN6_90P",
                "blueprint_name": 'Giữa học kỳ I',
                "duration_minutes": 90,
                "total_score": 10,
                "review_status": "APPROVED",
                "locked_at": "2026-08-26T00:00:00Z",
                "assessment_blueprints": {
                    "blueprint_code": "TOAN6_GHK1",
                    "grade_level": 6,
                    "owner_user_id": USER_ID,
                    "lifecycle_status": "ACTIVE",
                },
            }
        ]
    )

    options = SupabaseAssessmentGenerationCatalog(
        client=client,
        user_id=USER_ID,
    ).list_blueprints()

    assert len(options) == 1
    assert options[0].blueprint_code == "TOAN6_GHK1"
    assert options[0].grade_level == 6
    assert client.table_name == "assessment_blueprint_versions"
    assert ("eq", "review_status", "APPROVED") in client.query.operations
    assert (
        "eq",
        "assessment_blueprints.lifecycle_status",
        "ACTIVE",
    ) in client.query.operations
    assert ("not_is", "locked_at", "null") in client.query.operations


def test_catalog_accepts_empty_state() -> None:
    client = _Client([])
    options = SupabaseAssessmentGenerationCatalog(
        client=client,
        user_id=USER_ID,
    ).list_blueprints()
    assert options == ()


def test_page_uses_existing_generation_service_contract() -> None:
    text = UI_FILE.read_text(encoding="utf-8")
    assert "AssessmentExamGenerationRequest" in text
    assert "AssessmentExamGenerationService" in text
    assert "SupabaseAssessmentExamGenerationGateway" in text
    assert ".generate(request=request)" in text


def test_page_does_not_approve_publish_variant_or_export() -> None:
    text = UI_FILE.read_text(encoding="utf-8")
    for forbidden in (
        "apply_assessment_exam_review",
        "publish_assessment_exam",
        "create_assessment_exam_variants",
        "AssessmentDocumentExportService",
        ".insert(",
        ".update(",
        ".delete(",
        "service_role",
    ):
        assert forbidden not in text


def test_submit_for_review_requires_explicit_teacher_choice() -> None:
    text = UI_FILE.read_text(encoding="utf-8")
    assert '"Gửi duyệt ngay khi bản nháp hợp lệ"' in text
    assert "value=False" in text
    assert "submit_for_review=submit_for_review" in text


def test_teacher_portal_wires_generation_before_export() -> None:
    text = APP_FILE.read_text(encoding="utf-8-sig")
    assert "'T\\u1ea1o \\u0111\\u1ec1 ki\\u1ec3m tra'" in text
    assert 'selected == "Tạo đề kiểm tra"' in text
    assert "render_assessment_exam_generation_page" in text
    assert text.index('selected == "Tạo đề kiểm tra"') < text.index(
        'selected == "Xuất đề kiểm tra"'
    )
