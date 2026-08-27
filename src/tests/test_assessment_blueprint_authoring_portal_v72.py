from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from portal_v2.ui.assessment_blueprint_authoring_streamlit import (
    AssessmentBlueprintAuthoringError,
    _assignment_rows,
    _build_assignments,
)


ROOT = Path(__file__).resolve().parents[1]
UI_FILE = ROOT / "portal_v2" / "ui" / (
    "assessment_blueprint_authoring_streamlit.py"
)
APP_FILE = ROOT.parent / "scripts" / "teacher_portal" / "app.py"
ADMIN_UI_FILE = ROOT / "portal_v2" / "ui" / (
    "admin_assessment_template_workflow_streamlit.py"
)


def test_assignment_editor_preserves_existing_values_and_adds_defaults() -> None:
    rows = _assignment_rows(
        requirement_codes=("REQ-1", "REQ-2"),
        existing_links=(
            {
                "requirement_code": "REQ-1",
                "coverage_role": "SUPPORTING",
                "target_question_count": 3,
                "target_score": "1.50",
                "sequence_number": 40,
                "specification_note": "Đã lưu",
            },
        ),
    )

    assert rows[0] == {
        "requirement_code": "REQ-1",
        "coverage_role": "SUPPORTING",
        "target_question_count": 3,
        "target_score": "1.50",
        "sequence_number": 40,
        "specification_note": "Đã lưu",
    }
    assert rows[1]["coverage_role"] == "PRIMARY"
    assert rows[1]["target_question_count"] == 1
    assert rows[1]["target_score"] is None


def test_editor_rows_build_decimal_safe_domain_assignments() -> None:
    assignments = _build_assignments(
        (
            {
                "requirement_code": "REQ-1",
                "coverage_role": "primary",
                "target_question_count": 2,
                "target_score": "0.50",
                "sequence_number": 10,
                "specification_note": "Trọng tâm",
            },
        )
    )

    assert assignments[0].coverage_role == "PRIMARY"
    assert assignments[0].target_score == Decimal("0.50")
    assert assignments[0].as_rpc_record()["target_score"] == "0.50"


def test_editor_rejects_invalid_target_score() -> None:
    with pytest.raises(
        AssessmentBlueprintAuthoringError,
        match="Điểm mục tiêu",
    ):
        _build_assignments(
            (
                {
                    "requirement_code": "REQ-1",
                    "coverage_role": "PRIMARY",
                    "target_question_count": 1,
                    "target_score": "không-phải-số",
                    "sequence_number": 10,
                },
            )
        )


def test_page_uses_canonical_read_selection_and_atomic_link_services() -> None:
    text = UI_FILE.read_text(encoding="utf-8")

    required = (
        "SupabaseAssessmentCurriculumCatalog",
        "AssessmentCurriculumQueryService",
        "CanonicalAssessmentSelectionService",
        "expand_topic_descendants_explicitly",
        "finalize_selection",
        "BlueprintRequirementLinkService",
        "SupabaseBlueprintRequirementLinkGateway",
        ".replace_from_selection(",
    )
    for contract in required:
        assert contract in text


def test_page_does_not_read_canonical_json_or_write_link_table_directly() -> None:
    text = UI_FILE.read_text(encoding="utf-8")

    forbidden = (
        "learning_requirements.json",
        "curriculum_nodes.json",
        ".insert(",
        ".update(",
        ".delete(",
        "service_role",
    )
    for contract in forbidden:
        assert contract not in text


def test_teacher_portal_places_blueprint_before_exam_generation() -> None:
    text = APP_FILE.read_text(encoding="utf-8-sig")

    assert "'Ma tr\\u1eadn & b\\u1ea3n \\u0111\\u1eb7c t\\u1ea3'" in text
    assert 'selected == "Ma trận & bản đặc tả"' in text
    assert "render_assessment_blueprint_authoring_page" in text
    assert text.index('selected == "Ma trận & bản đặc tả"') < text.index(
        'selected == "Tạo đề kiểm tra"'
    )


def test_admin_portal_explicitly_activates_data_configured_profile() -> None:
    text = ADMIN_UI_FILE.read_text(encoding="utf-8")

    assert "_render_assessment_profile_activation" in text
    assert 'function_name="activate_assessment_profile"' in text
    assert 'disabled=profile.status != "DRAFT"' in text
    assert "Hồ sơ đang hoạt động" in text
