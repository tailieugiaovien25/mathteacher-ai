from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import portal_v2.ui.assessment_builder_streamlit as ui


class FakeSt:
    def __init__(self, initial=None):
        self.session_state = dict(initial or {})


def test_suggestion_state_is_separate_from_teacher_final_selection():
    st = FakeSt(
        {"math69_builder_requirements": "YCCD-MANUAL-1"}
    )

    ui._store_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
        requirement_codes=(
            "YCCD-MATH-07-0001",
            "YCCD-MATH-07-0002",
        ),
    )

    assert (
        st.session_state["math69_builder_requirements"]
        == "YCCD-MANUAL-1"
    )


def test_explicit_apply_copies_current_suggestion_to_teacher_selection():
    st = FakeSt()

    ui._store_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
        requirement_codes=(
            "YCCD-MATH-07-0001",
            "YCCD-MATH-07-0002",
        ),
    )

    applied = ui._apply_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
    )

    assert applied is True
    assert (
        st.session_state["math69_builder_requirements"]
        == "YCCD-MATH-07-0001, YCCD-MATH-07-0002"
    )


def test_stale_scope_token_cannot_overwrite_teacher_selection():
    st = FakeSt(
        {"math69_builder_requirements": "YCCD-MANUAL-KEEP"}
    )

    ui._store_requirement_recommendation_state(
        st=st,
        scope_token="scope-old",
        requirement_codes=("YCCD-MATH-07-0001",),
    )

    applied = ui._apply_requirement_recommendation_state(
        st=st,
        scope_token="scope-new",
    )

    assert applied is False
    assert (
        st.session_state["math69_builder_requirements"]
        == "YCCD-MANUAL-KEEP"
    )


def test_clear_suggestion_does_not_clear_teacher_selection():
    st = FakeSt(
        {"math69_builder_requirements": "YCCD-MANUAL-KEEP"}
    )

    ui._store_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
        requirement_codes=("YCCD-MATH-07-0001",),
    )

    ui._clear_requirement_recommendation_state(
        st=st,
    )

    assert (
        st.session_state["math69_builder_requirements"]
        == "YCCD-MANUAL-KEEP"
    )


def test_unproven_grade_fails_closed_before_runtime_call():
    st = FakeSt()

    result, error = ui._automatic_requirement_recommendation(
        st=st,
        ppct_runtime_evidence=SimpleNamespace(
            academic_year="2026-2027",
            source_id="source",
            source_version="1",
        ),
        ppct_suggestion=SimpleNamespace(
            grade_level=8,
            subject_grade="Toan 8",
            sub_subject=None,
            period_from=1,
            period_to=10,
        ),
    )

    assert result is None
    assert error == "Chưa đủ dữ liệu để đề xuất."


def test_ui_source_keeps_teacher_selection_as_final_configuration_authority():
    source = Path(ui.__file__).read_text(
        encoding="utf-8-sig"
    )

    assert (
        "selected_requirement_codes=_codes(requirement_text)"
        in source
    )
    assert "suggested_requirement_codes=" not in source
    assert "Áp dụng đề xuất YCCĐ" in source
    assert "YCCĐ hệ thống đề xuất" in source



def test_topic_suggestion_state_is_separate_from_teacher_final_selection():
    st = FakeSt({"math69_builder_topics": "TOPIC-MANUAL-KEEP"})

    ui._store_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
        requirement_codes=("Y1",),
    )
    ui._store_topic_recommendation_state(
        st=st,
        topic_codes=("T1", "T2"),
    )

    assert st.session_state["math69_builder_topics"] == "TOPIC-MANUAL-KEEP"


def test_explicit_topic_apply_requires_current_scope_token():
    st = FakeSt({"math69_builder_topics": "TOPIC-MANUAL-KEEP"})

    ui._store_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
        requirement_codes=("Y1",),
    )
    ui._store_topic_recommendation_state(
        st=st,
        topic_codes=("T1", "T2"),
    )

    assert ui._apply_topic_recommendation_state(
        st=st,
        scope_token="scope-old",
    ) is False
    assert st.session_state["math69_builder_topics"] == "TOPIC-MANUAL-KEEP"

    assert ui._apply_topic_recommendation_state(
        st=st,
        scope_token="scope-a",
    ) is True
    assert st.session_state["math69_builder_topics"] == "T1, T2"


def test_clear_suggestion_does_not_clear_teacher_topic_selection():
    st = FakeSt({"math69_builder_topics": "TOPIC-MANUAL-KEEP"})

    ui._store_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
        requirement_codes=("Y1",),
    )
    ui._store_topic_recommendation_state(
        st=st,
        topic_codes=("T1",),
    )
    ui._clear_requirement_recommendation_state(st=st)

    assert st.session_state["math69_builder_topics"] == "TOPIC-MANUAL-KEEP"
    assert (
        ui._ASSESSMENT_TOPIC_SUGGESTION_CODES_SESSION_KEY
        not in st.session_state
    )


def test_source_exposes_human_readable_sgk_topic_and_yccd_presentation():
    source = ui.__file__
    text = __import__("pathlib").Path(source).read_text(encoding="utf-8")

    assert "Bài SGK trong phạm vi đề xuất" in text
    assert "Chủ đề hệ thống đề xuất" in text
    assert "YCCĐ hệ thống đề xuất" in text
    assert "Áp dụng đề xuất Chủ đề" in text
    assert "runtime authenticated chỉ đọc Supabase" in text


# R55C4C14_HUMAN_READABLE_RECOMMENDATION_UI



def test_canonical_scope_confirmation_requires_both_explicit_apply_actions():
    st = FakeSt()

    ui._store_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
        requirement_codes=("Y1", "Y2"),
    )
    ui._store_topic_recommendation_state(
        st=st,
        topic_codes=("T1", "T2"),
    )

    assert ui._canonical_scope_selection_is_confirmed(
        st=st,
        topic_text="T1, T2",
        requirement_text="Y1, Y2",
        scope_token="scope-a",
    ) is False

    assert ui._apply_topic_recommendation_state(
        st=st,
        scope_token="scope-a",
    ) is True

    assert ui._canonical_scope_selection_is_confirmed(
        st=st,
        topic_text=st.session_state["math69_builder_topics"],
        requirement_text="Y1, Y2",
        scope_token="scope-a",
    ) is False

    assert ui._apply_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
    ) is True

    assert ui._canonical_scope_selection_is_confirmed(
        st=st,
        topic_text=st.session_state["math69_builder_topics"],
        requirement_text=st.session_state["math69_builder_requirements"],
        scope_token="scope-a",
    ) is True


def test_canonical_scope_confirmation_fails_closed_for_stale_or_edited_scope():
    st = FakeSt()

    ui._store_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
        requirement_codes=("Y1", "Y2"),
    )
    ui._store_topic_recommendation_state(
        st=st,
        topic_codes=("T1", "T2"),
    )
    ui._apply_topic_recommendation_state(st=st, scope_token="scope-a")
    ui._apply_requirement_recommendation_state(
        st=st,
        scope_token="scope-a",
    )

    assert ui._canonical_scope_selection_is_confirmed(
        st=st,
        topic_text="T1, T2",
        requirement_text="Y1, Y2",
        scope_token="scope-new",
    ) is False

    assert ui._canonical_scope_selection_is_confirmed(
        st=st,
        topic_text="T1, T2",
        requirement_text="Y1, Y2, Y-MANUAL",
        scope_token="scope-a",
    ) is False


def test_ui_preserves_preliminary_authority_and_adds_scope_confirmation():
    from pathlib import Path

    source = Path(ui.__file__).read_text(encoding="utf-8")

    assert "specification_preview.authority_label" in source
    assert "specification_preview.authority_note" in source
    assert (
        "Phạm vi canonical exact-reviewed đã được "
        "giáo viên xác nhận"
    ) in source
    assert (
        "Bản đặc tả vẫn là bản sơ bộ"
    ) in source


# R55C4C15_R6_CANONICAL_SCOPE_STATUS_UI
