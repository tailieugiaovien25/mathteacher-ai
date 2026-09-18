from decimal import Decimal
from types import SimpleNamespace

import pytest

from portal_v2.runtime.assessment_builder_governed_defaults_runtime import (
    AssessmentBuilderGovernedDefaultsRuntime,
    AssessmentBuilderGovernedDefaultsRuntimeError,
)


USER_ID = "11111111-1111-1111-1111-111111111111"


class _NotProxy:
    def __init__(self, query):
        self._query = query

    def is_(self, field, value):
        self._query.calls.append(
            ("not_is", field, value)
        )
        return self._query


class _Query:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []
        self.not_ = _NotProxy(self)

    def select(self, value):
        self.calls.append(
            ("select", value)
        )
        return self

    def eq(self, field, value):
        self.calls.append(
            ("eq", field, value)
        )
        return self

    def order(self, field, **kwargs):
        self.calls.append(
            ("order", field, kwargs)
        )
        return self

    def execute(self):
        return SimpleNamespace(
            data=self.rows
        )


class _Client:
    def __init__(self, tables):
        self.tables = tables
        self.queries = {}

    def table(self, name):
        query = _Query(
            self.tables.get(
                name,
                [],
            )
        )
        self.queries.setdefault(
            name,
            [],
        ).append(query)
        return query


def _setting_row(
    *,
    setting_id="SETTING-1",
    grade=8,
    semester=1,
    owner=USER_ID,
    visibility="PRIVATE",
):
    return {
        "setting_version_id": setting_id,
        "profile_code": "MATH-THCS-01",
        "subject_code": "MATH",
        "grade_level": grade,
        "academic_year": "2026-2027",
        "semester_number": semester,
        "duration_minutes": 90,
        "total_score": "10",
        "review_status": "APPROVED",
        "locked_at": "2026-09-01T00:00:00Z",
        "assessment_exam_setting_sets": {
            "owner_user_id": owner,
            "visibility": visibility,
            "lifecycle_status": "ACTIVE",
        },
    }


def _tables(
    *,
    settings=None,
):
    return {
        "assessment_exam_setting_versions": (
            settings
            if settings is not None
            else [_setting_row()]
        ),
        "assessment_profile_sections": [
            {
                "section_code": "MCQ",
                "question_type_code": "MCQ",
                "sequence_number": 10,
                "question_count": 12,
                "response_count": 12,
                "section_score": "3",
            },
            {
                "section_code": "TF",
                "question_type_code": "TRUE_FALSE",
                "sequence_number": 20,
                "question_count": 2,
                "response_count": 8,
                "section_score": "2",
            },
            {
                "section_code": "SHORT",
                "question_type_code": "SHORT_ANSWER",
                "sequence_number": 30,
                "question_count": 4,
                "response_count": 4,
                "section_score": "2",
            },
            {
                "section_code": "ESSAY",
                "question_type_code": "ESSAY",
                "sequence_number": 40,
                "question_count": 2,
                "response_count": 2,
                "section_score": "3",
            },
        ],
        "assessment_profile_level_allocations": [
            {
                "cognitive_level_code": "NB",
                "target_score": "4",
                "target_percentage": "40",
            },
            {
                "cognitive_level_code": "TH",
                "target_score": "3",
                "target_percentage": "30",
            },
            {
                "cognitive_level_code": "VD",
                "target_score": "3",
                "target_percentage": "30",
            },
        ],
    }


def test_runtime_loads_governed_defaults_end_to_end():
    client = _Client(
        _tables()
    )

    result = (
        AssessmentBuilderGovernedDefaultsRuntime(
            client=client,
            user_id=USER_ID,
        )
        .load_defaults(
            subject_code="MATH",
            grade_level=8,
            academic_year="2026-2027",
            semester_number=1,
        )
    )

    assert (
        result.setting_version_id
        == "SETTING-1"
    )
    assert result.profile_code == "MATH-THCS-01"
    assert result.defaults.duration_minutes == 90
    assert (
        result.defaults.total_score
        == Decimal("10")
    )
    assert (
        len(result.defaults.sections)
        == 4
    )
    assert (
        len(
            result.defaults
            .cognitive_allocations
        )
        == 3
    )


def test_shared_setting_from_other_owner_is_visible():
    client = _Client(
        _tables(
            settings=[
                _setting_row(
                    owner=(
                        "22222222-2222-2222-"
                        "2222-222222222222"
                    ),
                    visibility="SHARED",
                )
            ]
        )
    )

    result = (
        AssessmentBuilderGovernedDefaultsRuntime(
            client=client,
            user_id=USER_ID,
        )
        .load_defaults(
            subject_code="MATH",
            grade_level=8,
            academic_year="2026-2027",
            semester_number=1,
        )
    )

    assert (
        result.setting_version_id
        == "SETTING-1"
    )


def test_private_setting_from_other_owner_is_not_visible():
    client = _Client(
        _tables(
            settings=[
                _setting_row(
                    owner=(
                        "22222222-2222-2222-"
                        "2222-222222222222"
                    ),
                    visibility="PRIVATE",
                )
            ]
        )
    )

    with pytest.raises(
        AssessmentBuilderGovernedDefaultsRuntimeError,
        match="no approved setting",
    ):
        (
            AssessmentBuilderGovernedDefaultsRuntime(
                client=client,
                user_id=USER_ID,
            )
            .load_defaults(
                subject_code="MATH",
                grade_level=8,
                academic_year="2026-2027",
                semester_number=1,
            )
        )


def test_multiple_matching_approved_settings_fail_closed():
    client = _Client(
        _tables(
            settings=[
                _setting_row(
                    setting_id="SETTING-A",
                ),
                _setting_row(
                    setting_id="SETTING-B",
                ),
            ]
        )
    )

    with pytest.raises(
        AssessmentBuilderGovernedDefaultsRuntimeError,
        match="ambiguous",
    ):
        (
            AssessmentBuilderGovernedDefaultsRuntime(
                client=client,
                user_id=USER_ID,
            )
            .load_defaults(
                subject_code="MATH",
                grade_level=8,
                academic_year="2026-2027",
                semester_number=1,
            )
        )


def test_profile_score_mismatch_fails_closed():
    tables = _tables()
    tables[
        "assessment_profile_sections"
    ][-1]["section_score"] = "2"

    client = _Client(tables)

    with pytest.raises(
        AssessmentBuilderGovernedDefaultsRuntimeError,
        match="section scores",
    ):
        (
            AssessmentBuilderGovernedDefaultsRuntime(
                client=client,
                user_id=USER_ID,
            )
            .load_defaults(
                subject_code="MATH",
                grade_level=8,
                academic_year="2026-2027",
                semester_number=1,
            )
        )


def test_runtime_is_read_only_query_contract():
    client = _Client(
        _tables()
    )

    (
        AssessmentBuilderGovernedDefaultsRuntime(
            client=client,
            user_id=USER_ID,
        )
        .load_defaults(
            subject_code="MATH",
            grade_level=8,
            academic_year="2026-2027",
            semester_number=1,
        )
    )

    assert set(client.queries) == {
        "assessment_exam_setting_versions",
        "assessment_profile_sections",
        "assessment_profile_level_allocations",
    }

    for query_list in client.queries.values():
        for query in query_list:
            assert not any(
                call[0]
                in {
                    "insert",
                    "update",
                    "delete",
                    "upsert",
                    "rpc",
                }
                for call in query.calls
            )
