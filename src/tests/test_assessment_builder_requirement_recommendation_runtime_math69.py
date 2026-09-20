from types import SimpleNamespace

import pytest

from portal_v2.runtime.assessment_builder_requirement_recommendation_runtime import (
    BRIDGE_RPC_NAME,
    RECOMMENDATION_RPC_NAME,
    AssessmentBuilderRequirementRecommendationRuntime,
    AssessmentBuilderRequirementRecommendationRuntimeError,
)


USER_ID = "11111111-1111-1111-1111-111111111111"
CANDIDATE_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CANDIDATE_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
REVIEW_A = "cccccccc-cccc-cccc-cccc-cccccccccccc"
REVIEW_B = "dddddddd-dddd-dddd-dddd-dddddddddddd"


class _RpcQuery:
    def __init__(self, *, rows):
        self._rows = rows

    def execute(self):
        if isinstance(self._rows, Exception):
            raise self._rows

        return SimpleNamespace(
            data=self._rows
        )


class _Client:
    def __init__(self, *, responses):
        self.responses = responses
        self.calls = []

    def rpc(self, name, params):
        self.calls.append(
            (name, params)
        )
        return _RpcQuery(
            rows=self.responses[name]
        )


def _lesson_rows():
    return [
        {
            "textbook_unit_id":
                "unit-math-kntt-g7-lesson-001",
            "lesson_number": 1,
            "lesson_title":
                "Bài 1. Tập hợp các số hữu tỉ",
            "first_period": 1,
            "last_period": 2,
        },
        {
            "textbook_unit_id":
                "unit-math-kntt-g7-lesson-002",
            "lesson_number": 2,
            "lesson_title":
                "Bài 2. Cộng, trừ, nhân, chia số hữu tỉ",
            "first_period": 3,
            "last_period": 4,
        },
    ]


def _recommendation_rows():
    return [
        {
            "textbook_unit_id":
                "unit-math-kntt-g7-lesson-002",
            "requirement_code":
                "YCCD-MATH-07-0003",
            "candidate_id": CANDIDATE_B,
            "review_id": REVIEW_B,
            "reviewed_at": "2026-09-20T00:00:00Z",
        },
        {
            "textbook_unit_id":
                "unit-math-kntt-g7-lesson-001",
            "requirement_code":
                "YCCD-MATH-07-0001",
            "candidate_id": CANDIDATE_A,
            "review_id": REVIEW_A,
            "reviewed_at": "2026-09-20T00:00:00Z",
        },
        {
            "textbook_unit_id":
                "unit-math-kntt-g7-lesson-001",
            "requirement_code":
                "YCCD-MATH-07-0002",
            "candidate_id":
                "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            "review_id":
                "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "reviewed_at": "2026-09-20T00:00:00Z",
        },
    ]


def _runtime(*, lessons=None, recommendations=None):
    client = _Client(
        responses={
            BRIDGE_RPC_NAME: (
                _lesson_rows()
                if lessons is None
                else lessons
            ),
            RECOMMENDATION_RPC_NAME: (
                _recommendation_rows()
                if recommendations is None
                else recommendations
            ),
        }
    )

    return (
        AssessmentBuilderRequirementRecommendationRuntime(
            client=client,
            user_id=USER_ID,
        ),
        client,
    )


def test_runtime_composes_exact_bridge_and_recommendation_rpcs():
    runtime, client = _runtime()

    result = runtime.recommend(
        source_id="ppct-source-1",
        source_version="1",
        subject_grade="Toán 7",
        sub_subject=None,
        period_from=1,
        period_to=4,
    )

    assert result.textbook_unit_ids == (
        "unit-math-kntt-g7-lesson-001",
        "unit-math-kntt-g7-lesson-002",
    )
    assert result.requirement_codes == (
        "YCCD-MATH-07-0001",
        "YCCD-MATH-07-0002",
        "YCCD-MATH-07-0003",
    )
    assert result.status == (
        "EXACT_REVIEWED_RECOMMENDATION"
    )

    assert client.calls == [
        (
            BRIDGE_RPC_NAME,
            {
                "target_source_id": "ppct-source-1",
                "target_payload_version": "1",
                "target_subject_grade": "Toán 7",
                "target_sub_subject": "",
                "target_period_from": 1,
                "target_period_to": 4,
            },
        ),
        (
            RECOMMENDATION_RPC_NAME,
            {
                "target_textbook_unit_ids": [
                    "unit-math-kntt-g7-lesson-001",
                    "unit-math-kntt-g7-lesson-002",
                ]
            },
        ),
    ]


def test_empty_bridge_fails_closed_without_second_rpc():
    runtime, client = _runtime(
        lessons=[],
    )

    with pytest.raises(
        AssessmentBuilderRequirementRecommendationRuntimeError,
        match="no reviewed textbook lessons",
    ):
        runtime.recommend(
            source_id="ppct-source-1",
            source_version="1",
            subject_grade="Toán 7",
            sub_subject=None,
            period_from=1,
            period_to=4,
        )

    assert len(client.calls) == 1
    assert client.calls[0][0] == BRIDGE_RPC_NAME


def test_empty_recommendations_fail_closed():
    runtime, _ = _runtime(
        recommendations=[],
    )

    with pytest.raises(
        AssessmentBuilderRequirementRecommendationRuntimeError,
        match="no exact reviewed requirement recommendations",
    ):
        runtime.recommend(
            source_id="ppct-source-1",
            source_version="1",
            subject_grade="Toán 7",
            sub_subject=None,
            period_from=1,
            period_to=4,
        )


def test_recommendation_outside_ppct_scope_fails_closed():
    rows = _recommendation_rows()
    rows.append(
        {
            "textbook_unit_id":
                "unit-math-kntt-g7-lesson-003",
            "requirement_code":
                "YCCD-MATH-07-0004",
            "candidate_id":
                "12121212-1212-1212-1212-121212121212",
            "review_id":
                "34343434-3434-3434-3434-343434343434",
        }
    )

    runtime, _ = _runtime(
        recommendations=rows,
    )

    with pytest.raises(
        AssessmentBuilderRequirementRecommendationRuntimeError,
        match="outside PPCT scope",
    ):
        runtime.recommend(
            source_id="ppct-source-1",
            source_version="1",
            subject_grade="Toán 7",
            sub_subject=None,
            period_from=1,
            period_to=4,
        )


def test_lesson_without_recommendation_fails_closed():
    runtime, _ = _runtime(
        recommendations=[
            {
                "textbook_unit_id":
                    "unit-math-kntt-g7-lesson-001",
                "requirement_code":
                    "YCCD-MATH-07-0001",
                "candidate_id": CANDIDATE_A,
                "review_id": REVIEW_A,
            }
        ],
    )

    with pytest.raises(
        AssessmentBuilderRequirementRecommendationRuntimeError,
        match="one or more PPCT lessons have no exact reviewed",
    ):
        runtime.recommend(
            source_id="ppct-source-1",
            source_version="1",
            subject_grade="Toán 7",
            sub_subject=None,
            period_from=1,
            period_to=4,
        )


def test_duplicate_lesson_requirement_pair_fails_closed():
    duplicate = {
        "textbook_unit_id":
            "unit-math-kntt-g7-lesson-001",
        "requirement_code":
            "YCCD-MATH-07-0001",
        "candidate_id":
            "56565656-5656-5656-5656-565656565656",
        "review_id":
            "78787878-7878-7878-7878-787878787878",
    }

    runtime, _ = _runtime(
        recommendations=(
            _recommendation_rows()
            + [duplicate]
        ),
    )

    with pytest.raises(
        AssessmentBuilderRequirementRecommendationRuntimeError,
        match="duplicate lesson/requirement",
    ):
        runtime.recommend(
            source_id="ppct-source-1",
            source_version="1",
            subject_grade="Toán 7",
            sub_subject=None,
            period_from=1,
            period_to=4,
        )


def test_lesson_period_outside_requested_scope_fails_closed():
    lessons = _lesson_rows()
    lessons[0] = {
        **lessons[0],
        "first_period": 0,
    }

    runtime, _ = _runtime(
        lessons=lessons,
    )

    with pytest.raises(
        AssessmentBuilderRequirementRecommendationRuntimeError,
        match="first_period must be a positive integer",
    ):
        runtime.recommend(
            source_id="ppct-source-1",
            source_version="1",
            subject_grade="Toán 7",
            sub_subject=None,
            period_from=1,
            period_to=4,
        )


def test_rpc_failure_is_wrapped_fail_closed():
    runtime, _ = _runtime(
        lessons=RuntimeError("network down"),
    )

    with pytest.raises(
        AssessmentBuilderRequirementRecommendationRuntimeError,
        match="PPCT lesson bridge RPC failed",
    ):
        runtime.recommend(
            source_id="ppct-source-1",
            source_version="1",
            subject_grade="Toán 7",
            sub_subject=None,
            period_from=1,
            period_to=4,
        )


def test_invalid_user_id_is_rejected_before_rpc():
    client = _Client(
        responses={}
    )

    with pytest.raises(
        ValueError,
        match="user_id must be a valid UUID",
    ):
        AssessmentBuilderRequirementRecommendationRuntime(
            client=client,
            user_id="not-a-uuid",
        )
