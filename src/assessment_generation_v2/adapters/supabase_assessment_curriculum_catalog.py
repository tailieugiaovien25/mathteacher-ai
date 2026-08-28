"""Supabase adapter for canonical assessment curriculum reads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentCurriculumProgram,
    AssessmentCurriculumQueryError,
    AssessmentCurriculumTopic,
    AssessmentLearningRequirement,
)


def _data(response: Any) -> Any:
    if hasattr(response, "data"):
        return response.data

    if isinstance(response, Mapping):
        return response.get("data")

    raise AssessmentCurriculumQueryError(
        "Supabase response has no data"
    )


def _rows(response: Any) -> list[Mapping[str, Any]]:
    value = _data(response)

    if value is None:
        return []

    if not isinstance(value, list):
        raise AssessmentCurriculumQueryError(
            "Supabase response data must be a list"
        )

    rows: list[Mapping[str, Any]] = []

    for item in value:
        if not isinstance(item, Mapping):
            raise AssessmentCurriculumQueryError(
                "Supabase row must be a mapping"
            )

        rows.append(item)

    return rows


def _text(
    value: object,
    field_name: str,
) -> str:
    text = str(value or "").strip()

    if not text:
        raise AssessmentCurriculumQueryError(
            f"{field_name} is required"
        )

    return text


def _optional_text(
    value: object,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def _metadata(
    value: object,
) -> Mapping[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise AssessmentCurriculumQueryError(
            "metadata must be a mapping"
        )

    return value


class SupabaseAssessmentCurriculumCatalog:
    """Read-only adapter for assessment canonical curriculum."""

    PROGRAM_TABLE = "assessment_curriculum_programs"
    TOPIC_TABLE = "assessment_curriculum_topics"
    REQUIREMENT_TABLE = "assessment_learning_requirements"

    def __init__(
        self,
        *,
        client: Any,
    ) -> None:
        self._client = client

    def find_active_program(
        self,
        *,
        subject_code: str,
        grade_level: int,
    ) -> AssessmentCurriculumProgram | None:

        response = (
            self._client
            .table(self.PROGRAM_TABLE)
            .select(
                "program_code,"
                "program_name,"
                "subject_code,"
                "education_level,"
                "grade_min,"
                "grade_max,"
                "version_label,"
                "status"
            )
            .eq(
                "subject_code",
                subject_code,
            )
            .eq(
                "status",
                "ACTIVE",
            )
            .lte(
                "grade_min",
                int(grade_level),
            )
            .gte(
                "grade_max",
                int(grade_level),
            )
            .order(
                "program_code",
            )
            .execute()
        )

        rows = _rows(response)

        if not rows:
            return None

        if len(rows) != 1:
            raise AssessmentCurriculumQueryError(
                "Expected exactly one active curriculum program"
            )

        row = rows[0]

        return AssessmentCurriculumProgram(
            program_code=_text(
                row.get("program_code"),
                "program_code",
            ),
            program_name=_text(
                row.get("program_name"),
                "program_name",
            ),
            subject_code=_text(
                row.get("subject_code"),
                "subject_code",
            ),
            education_level=_text(
                row.get("education_level"),
                "education_level",
            ),
            grade_min=int(row.get("grade_min")),
            grade_max=int(row.get("grade_max")),
            version_label=_text(
                row.get("version_label"),
                "version_label",
            ),
            status=_text(
                row.get("status"),
                "status",
            ),
        )

    def list_topics(
        self,
        *,
        program_code: str,
        grade_level: int,
    ) -> tuple[AssessmentCurriculumTopic, ...]:

        response = (
            self._client
            .table(self.TOPIC_TABLE)
            .select(
                "topic_code,"
                "program_code,"
                "parent_topic_code,"
                "grade_level,"
                "domain_code,"
                "topic_name,"
                "sequence_number,"
                "status,"
                "metadata"
            )
            .eq(
                "program_code",
                program_code,
            )
            .eq(
                "grade_level",
                int(grade_level),
            )
            .eq(
                "status",
                "ACTIVE",
            )
            .like(
                "topic_code",
                "CURR-NODE-%",
            )
            .order(
                "sequence_number",
            )
            .order(
                "topic_code",
            )
            .execute()
        )

        result = []

        for row in _rows(response):
            metadata = _metadata(
                row.get("metadata")
            )

            canonical_node_type = _optional_text(
                metadata.get(
                    "canonical_node_type"
                )
            )

            if canonical_node_type is None:
                raise AssessmentCurriculumQueryError(
                    "Canonical topic is missing "
                    "metadata.canonical_node_type: "
                    + _text(
                        row.get("topic_code"),
                        "topic_code",
                    )
                )

            result.append(
                AssessmentCurriculumTopic(
                    topic_code=_text(
                        row.get("topic_code"),
                        "topic_code",
                    ),
                    program_code=_text(
                        row.get("program_code"),
                        "program_code",
                    ),
                    parent_topic_code=_optional_text(
                        row.get("parent_topic_code")
                    ),
                    grade_level=int(
                        row.get("grade_level")
                    ),
                    domain_code=_text(
                        row.get("domain_code"),
                        "domain_code",
                    ),
                    topic_name=_text(
                        row.get("topic_name"),
                        "topic_name",
                    ),
                    sequence_number=int(
                        row.get("sequence_number")
                    ),
                    status=_text(
                        row.get("status"),
                        "status",
                    ),
                    canonical_node_type=canonical_node_type,
                )
            )

        return tuple(result)

    def list_requirements(
        self,
        *,
        program_code: str,
        grade_level: int,
        topic_codes: Sequence[str] | None = None,
    ) -> tuple[AssessmentLearningRequirement, ...]:

        query = (
            self._client
            .table(self.REQUIREMENT_TABLE)
            .select(
                "requirement_code,"
                "program_code,"
                "topic_code,"
                "grade_level,"
                "requirement_text,"
                "source_locator,"
                "version_number,"
                "status,"
                "metadata"
            )
            .eq(
                "program_code",
                program_code,
            )
            .eq(
                "grade_level",
                int(grade_level),
            )
            .eq(
                "status",
                "ACTIVE",
            )
            .eq(
                "metadata->>canonical_status",
                "VERIFIED",
            )
        )

        if topic_codes is not None:
            values = list(
                dict.fromkeys(topic_codes)
            )

            if not values:
                return ()

            query = query.in_(
                "topic_code",
                values,
            )

        response = (
            query
            .order(
                "topic_code",
            )
            .order(
                "requirement_code",
            )
            .execute()
        )

        result = []

        for row in _rows(response):
            metadata = _metadata(
                row.get("metadata")
            )

            canonical_status = _optional_text(
                metadata.get(
                    "canonical_status"
                )
            )

            if canonical_status != "VERIFIED":
                raise AssessmentCurriculumQueryError(
                    "Requirement is not VERIFIED canonical: "
                    + _text(
                        row.get("requirement_code"),
                        "requirement_code",
                    )
                )

            result.append(
                AssessmentLearningRequirement(
                    requirement_code=_text(
                        row.get("requirement_code"),
                        "requirement_code",
                    ),
                    program_code=_text(
                        row.get("program_code"),
                        "program_code",
                    ),
                    topic_code=_text(
                        row.get("topic_code"),
                        "topic_code",
                    ),
                    grade_level=int(
                        row.get("grade_level")
                    ),
                    requirement_text=_text(
                        row.get("requirement_text"),
                        "requirement_text",
                    ),
                    source_locator=_optional_text(
                        row.get("source_locator")
                    ),
                    version_number=int(
                        row.get("version_number")
                    ),
                    status=_text(
                        row.get("status"),
                        "status",
                    ),
                    canonical_status=canonical_status,
                )
            )

        return tuple(result)
