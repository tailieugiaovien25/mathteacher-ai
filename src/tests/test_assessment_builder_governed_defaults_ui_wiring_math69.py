from decimal import Decimal
from types import SimpleNamespace

import portal_v2.ui.assessment_builder_streamlit as ui
from assessment_generation_v2.services.assessment_builder_governed_defaults_service import (
    AssessmentBuilderGovernedDefaults,
    GovernedAssessmentSectionSnapshot,
    GovernedAssessmentSettingSnapshot,
    GovernedCognitiveAllocationSnapshot,
)
from portal_v2.runtime.assessment_ppct_session_bridge import (
    AssessmentPpctRuntimeEvidence,
)


USER_ID = "11111111-1111-1111-1111-111111111111"


class _St:
    def __init__(self):
        self.session_state = {
            "portal_supabase_client": object(),
            "portal_user_id": USER_ID,
        }


def _defaults():
    return AssessmentBuilderGovernedDefaults(
        setting=GovernedAssessmentSettingSnapshot(
            setting_version_id="SETTING-1",
            profile_code="MATH-THCS-01",
            subject_code="MATH",
            assessment_type_code="FINAL",
            grade_level=8,
            academic_year="2026-2027",
            semester_number=1,
            duration_minutes=90,
            total_score=Decimal("10"),
        ),
        sections=(
            GovernedAssessmentSectionSnapshot(
                section_code="MCQ",
                question_type_code="MCQ",
                question_count=12,
                response_count=12,
                section_score=Decimal("3"),
            ),
            GovernedAssessmentSectionSnapshot(
                section_code="TF",
                question_type_code="TRUE_FALSE",
                question_count=2,
                response_count=8,
                section_score=Decimal("2"),
            ),
            GovernedAssessmentSectionSnapshot(
                section_code="SHORT",
                question_type_code="SHORT_ANSWER",
                question_count=4,
                response_count=4,
                section_score=Decimal("2"),
            ),
            GovernedAssessmentSectionSnapshot(
                section_code="ESSAY",
                question_type_code="ESSAY",
                question_count=2,
                response_count=2,
                section_score=Decimal("3"),
            ),
        ),
        cognitive_allocations=(
            GovernedCognitiveAllocationSnapshot(
                cognitive_level_code="NB",
                target_score=Decimal("4"),
                target_percentage=Decimal("40"),
            ),
            GovernedCognitiveAllocationSnapshot(
                cognitive_level_code="TH",
                target_score=Decimal("3"),
                target_percentage=Decimal("30"),
            ),
            GovernedCognitiveAllocationSnapshot(
                cognitive_level_code="VD",
                target_score=Decimal("3"),
                target_percentage=Decimal("30"),
            ),
        ),
    )


def test_auto_governed_defaults_uses_authenticated_session_and_ppct_year(
    monkeypatch,
):
    captured = {}

    class _Runtime:
        def __init__(self, *, client, user_id):
            captured["client"] = client
            captured["user_id"] = user_id

        def load_defaults(
            self,
            *,
            subject_code,
            assessment_type_code,
            grade_level,
            academic_year,
            semester_number,
        ):
            captured["subject_code"] = subject_code
            captured["assessment_type_code"] = assessment_type_code
            captured["grade_level"] = grade_level
            captured["academic_year"] = academic_year
            captured["semester_number"] = semester_number
            return SimpleNamespace(defaults=_defaults())

    monkeypatch.setattr(
        ui,
        "AssessmentBuilderGovernedDefaultsRuntime",
        _Runtime,
    )

    st = _St()
    evidence = AssessmentPpctRuntimeEvidence(
        academic_year="2026-2027",
        source_id="PPCT-1",
        source_version="7",
    )

    defaults, error = ui._automatic_governed_defaults(
        st=st,
        grade_level=8,
        assessment_type_code="FINAL",
        semester_number=1,
        ppct_runtime_evidence=evidence,
    )

    assert error is None
    assert defaults is not None
    assert defaults.duration_minutes == 90
    assert captured["client"] is st.session_state[
        "portal_supabase_client"
    ]
    assert captured["user_id"] == USER_ID
    assert captured["subject_code"] == "MATH"
    assert captured["assessment_type_code"] == "FINAL"
    assert captured["grade_level"] == 8
    assert captured["academic_year"] == "2026-2027"
    assert captured["semester_number"] == 1


def test_missing_portal_runtime_context_fails_closed():
    st = SimpleNamespace(session_state={})
    evidence = AssessmentPpctRuntimeEvidence(
        academic_year="2026-2027",
        source_id="PPCT-1",
        source_version="7",
    )

    defaults, error = ui._automatic_governed_defaults(
        st=st,
        grade_level=8,
        assessment_type_code="FINAL",
        semester_number=1,
        ppct_runtime_evidence=evidence,
    )

    assert defaults is None
    assert "authenticated portal runtime" in error


def test_missing_ppct_evidence_fails_closed():
    defaults, error = ui._automatic_governed_defaults(
        st=_St(),
        grade_level=8,
        assessment_type_code="FINAL",
        semester_number=1,
        ppct_runtime_evidence=None,
    )

    assert defaults is None
    assert "PPCT runtime evidence" in error


def test_governed_sections_map_profile_codes_to_builder_codes():
    sections = ui._governed_builder_sections(_defaults())

    assert [
        item.question_type_code
        for item in sections
    ] == [
        "MULTIPLE_CHOICE",
        "TRUE_FALSE",
        "SHORT_RESPONSE",
        "ESSAY",
    ]
    assert [
        item.question_count
        for item in sections
    ] == [12, 2, 4, 2]


def test_governed_cognitive_allocations_map_profile_codes():
    allocations = ui._governed_builder_allocations(
        _defaults()
    )

    assert [
        item.cognitive_level_code
        for item in allocations
    ] == [
        "KNOW",
        "UNDERSTAND",
        "APPLY",
    ]
    assert [
        item.target_percentage
        for item in allocations
    ] == [
        Decimal("40"),
        Decimal("30"),
        Decimal("30"),
    ]


def test_ui_no_longer_uses_manual_number_inputs():
    from pathlib import Path

    source = Path(
        "src/portal_v2/ui/"
        "assessment_builder_streamlit.py"
    ).read_text(encoding="utf-8-sig")

    assert "st.number_input(" not in source
    assert (
        "AssessmentBuilderGovernedDefaultsRuntime"
        in source
    )
    assert "portal_supabase_client" in source
    assert "portal_user_id" in source
    assert (
        "Hệ thống tự động lấy từ thiết đặt đã duyệt"
        in source
    )
