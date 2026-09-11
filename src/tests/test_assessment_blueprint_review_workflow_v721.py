from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assessment_generation_v2.services.assessment_matrix_cell_authoring import (
    build_default_matrix_cell_rows,
    matrix_cell_rows_payload,
)
from portal_v2.ui.assessment_blueprint_authoring_streamlit import (
    AssessmentProfileSectionOption,
    CognitiveLevelOption,
    ProfileLevelAllocation,
    _cell_payload,
    _default_cell_rows,
)


ROOT = Path(__file__).resolve().parents[1]
TEACHER_UI = (
    ROOT / "portal_v2" / "ui" /
    "assessment_blueprint_authoring_streamlit.py"
)
ADMIN_UI = (
    ROOT / "portal_v2" / "ui" /
    "admin_assessment_template_workflow_streamlit.py"
)
ADMIN_SHELL = ROOT / "portal_v2" / "ui" / "admin_shell.py"


def _sections() -> tuple[AssessmentProfileSectionOption, ...]:
    return (
        AssessmentProfileSectionOption(
            "MCQ", "Nhiều lựa chọn", "MULTIPLE_CHOICE",
            10, 12, 12, Decimal("3"),
        ),
        AssessmentProfileSectionOption(
            "TF", "Đúng sai", "TRUE_FALSE",
            20, 2, 8, Decimal("2"),
        ),
        AssessmentProfileSectionOption(
            "SHORT", "Trả lời ngắn", "SHORT_RESPONSE",
            30, 4, 4, Decimal("2"),
        ),
        AssessmentProfileSectionOption(
            "ESSAY", "Tự luận", "ESSAY",
            40, 2, 2, Decimal("3"),
        ),
    )


def _levels() -> tuple[CognitiveLevelOption, ...]:
    return (
        CognitiveLevelOption("KNOW", "Nhận biết", 10),
        CognitiveLevelOption("UNDERSTAND", "Thông hiểu", 20),
        CognitiveLevelOption("APPLY", "Vận dụng", 30),
    )


def test_default_cells_match_3223_sections_and_403030_levels() -> None:
    rows = _default_cell_rows(
        sections=_sections(),
        topic_codes=("TOPIC-1", "TOPIC-2"),
        cognitive_levels=_levels(),
        level_allocations=(
            ProfileLevelAllocation("KNOW", Decimal("4"), Decimal("40")),
            ProfileLevelAllocation(
                "UNDERSTAND", Decimal("3"), Decimal("30")
            ),
            ProfileLevelAllocation("APPLY", Decimal("3"), Decimal("30")),
        ),
        existing_cells=(),
    )

    assert sum(Decimal(str(row["target_score"])) for row in rows) == 10
    by_level = {
        level: sum(
            Decimal(str(row["target_score"]))
            for row in rows
            if row["cognitive_level_code"] == level
        )
        for level in ("KNOW", "UNDERSTAND", "APPLY")
    }
    assert by_level == {
        "KNOW": Decimal("4"),
        "UNDERSTAND": Decimal("3"),
        "APPLY": Decimal("3"),
    }
    for section in _sections():
        section_rows = [
            row for row in rows
            if row["section_code"] == section.section_code
        ]
        assert sum(row["question_count"] for row in section_rows) == (
            section.question_count
        )
        assert sum(row["response_count"] for row in section_rows) == (
            section.response_count
        )
        assert sum(
            Decimal(str(row["target_score"])) for row in section_rows
        ) == section.section_score


def test_cell_payload_is_decimal_safe_and_complete() -> None:
    payload = _cell_payload(
        (
            {
                "section_code": "MCQ",
                "topic_code": "TOPIC-1",
                "cognitive_level_code": "KNOW",
                "question_count": 12,
                "response_count": 12,
                "target_score": "3.00",
                "sequence_number": 10,
                "specification_note": "Trọng tâm",
            },
        )
    )
    assert payload[0]["target_score"] == "3.00"
    assert payload[0]["topic_code"] == "TOPIC-1"


def test_teacher_ui_saves_cells_and_submits_only_through_rpcs() -> None:
    text = TEACHER_UI.read_text(encoding="utf-8")
    assert 'REPLACE_CELLS_RPC = "replace_assessment_blueprint_cells"' in text
    assert 'SUBMIT_RPC = "submit_assessment_blueprint_for_review"' in text
    assert "assessment_blueprint_ready_for_review" in text
    assert "Gửi ma trận để duyệt" in text
    for forbidden in (".insert(", ".update(", ".delete(", "service_role"):
        assert forbidden not in text


def test_admin_ui_reviews_through_governed_rpc_and_receives_actor_id() -> None:
    text = ADMIN_UI.read_text(encoding="utf-8")
    shell = ADMIN_SHELL.read_text(encoding="utf-8")
    assert '"review_assessment_blueprint"' in text
    assert "Duyệt ma trận và bản đặc tả" in text
    assert "REVISION_REQUIRED" in text
    assert "REJECTED" in text
    assert "reviewer_user_id=authorization.user_id" in shell
    for forbidden in (".insert(", ".update(", ".delete(", "service_role"):
        assert forbidden not in text



def test_portal_default_cells_delegate_to_shared_matrix_service() -> None:
    kwargs = {
        "sections": _sections(),
        "topic_codes": ("TOPIC-1", "TOPIC-2"),
        "cognitive_levels": _levels(),
        "level_allocations": (
            ProfileLevelAllocation(
                "KNOW", Decimal("4"), Decimal("40")
            ),
            ProfileLevelAllocation(
                "UNDERSTAND", Decimal("3"), Decimal("30")
            ),
            ProfileLevelAllocation(
                "APPLY", Decimal("3"), Decimal("30")
            ),
        ),
        "existing_cells": (),
    }
    assert _default_cell_rows(**kwargs) == (
        build_default_matrix_cell_rows(**kwargs)
    )


def test_portal_default_cells_preserve_legacy_fraction_fallback() -> None:
    sections = (
        AssessmentProfileSectionOption(
            "ESSAY",
            "T? lu?n",
            "ESSAY",
            10,
            1,
            1,
            Decimal("1"),
        ),
    )
    levels = (
        CognitiveLevelOption("KNOW", "Nh?n bi?t", 10),
        CognitiveLevelOption("UNDERSTAND", "Th?ng hi?u", 20),
    )
    allocations = (
        ProfileLevelAllocation(
            "KNOW", Decimal("0.5"), Decimal("50")
        ),
        ProfileLevelAllocation(
            "UNDERSTAND", Decimal("0.5"), Decimal("50")
        ),
    )
    kwargs = {
        "sections": sections,
        "topic_codes": ("TOPIC-1",),
        "cognitive_levels": levels,
        "level_allocations": allocations,
        "existing_cells": (),
    }
    rows = _default_cell_rows(**kwargs)
    assert rows == build_default_matrix_cell_rows(**kwargs)
    assert rows == [
        {
            "section_code": "ESSAY",
            "topic_code": "TOPIC-1",
            "cognitive_level_code": "KNOW",
            "question_count": 1,
            "response_count": 1,
            "target_score": 1.0,
            "sequence_number": 10,
            "specification_note": "",
        }
    ]


def test_portal_cell_payload_delegates_to_shared_matrix_service() -> None:
    rows = (
        {
            "section_code": "MCQ",
            "topic_code": "TOPIC-1",
            "cognitive_level_code": "KNOW",
            "question_count": 12,
            "response_count": 12,
            "target_score": "3.00",
            "sequence_number": 10,
            "specification_note": "Tr?ng t?m",
        },
    )
    assert _cell_payload(rows) == matrix_cell_rows_payload(rows)


def test_teacher_ui_uses_shared_matrix_authoring_service() -> None:
    text = TEACHER_UI.read_text(encoding="utf-8")
    assert (
        "assessment_generation_v2.services."
        "assessment_matrix_cell_authoring"
    ) in text
    assert "build_default_matrix_cell_rows(" in text
    assert "matrix_cell_rows_payload(" in text
    assert "class AssessmentProfileSectionOption:" not in text
    assert "class CognitiveLevelOption:" not in text
    assert "class ProfileLevelAllocation:" not in text
