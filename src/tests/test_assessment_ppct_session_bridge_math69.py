import pytest

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from portal_v2.runtime.assessment_ppct_session_bridge import (
    ASSESSMENT_PPCT_EVIDENCE_SESSION_KEY,
    ASSESSMENT_PPCT_ROWS_SESSION_KEY,
    AssessmentPpctRuntimeEvidence,
    clear_assessment_ppct_rows,
    inject_assessment_ppct_rows,
)


def _rows():
    return (
        PPCTRow(
            subject_grade="Toan 8",
            period=1,
            lesson_name="Bai 1",
        ),
        PPCTRow(
            subject_grade="Toan 8",
            period=2,
            lesson_name="Bai 2",
        ),
    )


def test_runtime_bridge_injects_rows_and_evidence():
    session = {}
    rows = _rows()
    evidence = AssessmentPpctRuntimeEvidence(
        academic_year="2026-2027",
        source_id="SRC-PPCT-001",
        source_version="3",
    )

    inject_assessment_ppct_rows(
        session_state=session,
        rows=rows,
        evidence=evidence,
    )

    assert session[
        ASSESSMENT_PPCT_ROWS_SESSION_KEY
    ] == rows
    assert session[
        ASSESSMENT_PPCT_EVIDENCE_SESSION_KEY
    ] == evidence


def test_runtime_bridge_rejects_empty_rows():
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        inject_assessment_ppct_rows(
            session_state={},
            rows=(),
        )


def test_runtime_bridge_rejects_non_ppct_rows():
    with pytest.raises(
        TypeError,
        match="PPCTRow",
    ):
        inject_assessment_ppct_rows(
            session_state={},
            rows=("bad",),
        )


def test_runtime_bridge_clear_removes_both_keys():
    session = {}
    inject_assessment_ppct_rows(
        session_state=session,
        rows=_rows(),
        evidence=AssessmentPpctRuntimeEvidence(
            academic_year="2026-2027",
            source_id="SRC-PPCT-001",
            source_version="3",
        ),
    )

    clear_assessment_ppct_rows(
        session_state=session,
    )

    assert (
        ASSESSMENT_PPCT_ROWS_SESSION_KEY
        not in session
    )
    assert (
        ASSESSMENT_PPCT_EVIDENCE_SESSION_KEY
        not in session
    )
