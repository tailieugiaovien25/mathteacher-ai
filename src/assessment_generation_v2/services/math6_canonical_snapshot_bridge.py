"""Pure in-memory bridge from Math 6 MVP authoring to canonical snapshot schema 2."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Protocol, Sequence
from uuid import UUID

from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentCurriculumTopic,
    AssessmentLearningRequirement,
)
from assessment_generation_v2.services.assessment_matrix_cell_authoring import (
    AssessmentMatrixCell,
    AssessmentProfileSectionOption,
    CognitiveLevelOption,
)
from assessment_generation_v2.services.blueprint_requirement_link_service import (
    BlueprintRequirementAssignment,
)


class Math6CanonicalSnapshotBridgeError(ValueError):
    """Raised when Math 6 authoring data cannot form snapshot schema 2."""


def _text(value: object, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise Math6CanonicalSnapshotBridgeError(
            f"{field_name} is required"
        )
    return normalized


def _uuid(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    try:
        return str(UUID(text))
    except ValueError as error:
        raise Math6CanonicalSnapshotBridgeError(
            f"{field_name} must be a valid UUID"
        ) from error


def _positive_int(value: object, field_name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise Math6CanonicalSnapshotBridgeError(
            f"{field_name} must be an integer"
        ) from error
    if number <= 0:
        raise Math6CanonicalSnapshotBridgeError(
            f"{field_name} must be positive"
        )
    return number


def _score(value: object, field_name: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except Exception as error:
        raise Math6CanonicalSnapshotBridgeError(
            f"{field_name} must be numeric"
        ) from error
    if number <= 0:
        raise Math6CanonicalSnapshotBridgeError(
            f"{field_name} must be positive"
        )
    return number


def _json_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


@dataclass(frozen=True, slots=True)
class CanonicalRequirementCompetency:
    competency_code: str
    competency_name: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "competency_code",
            _text(self.competency_code, "competency_code").upper(),
        )
        object.__setattr__(
            self,
            "competency_name",
            _text(self.competency_name, "competency_name"),
        )

    def as_snapshot_record(self) -> dict[str, object]:
        return {
            "competency_code": self.competency_code,
            "competency_name": self.competency_name,
        }


@dataclass(frozen=True, slots=True)
class Math6CanonicalSnapshotIdentity:
    publication_id: str
    published_at: str
    exam_version_id: str
    blueprint_version_id: str
    exam_title: str
    duration_minutes: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "publication_id",
            _uuid(self.publication_id, "publication_id"),
        )
        object.__setattr__(
            self,
            "exam_version_id",
            _uuid(self.exam_version_id, "exam_version_id"),
        )
        object.__setattr__(
            self,
            "blueprint_version_id",
            _uuid(self.blueprint_version_id, "blueprint_version_id"),
        )
        object.__setattr__(
            self,
            "published_at",
            _text(self.published_at, "published_at"),
        )
        object.__setattr__(
            self,
            "exam_title",
            _text(self.exam_title, "exam_title"),
        )
        object.__setattr__(
            self,
            "duration_minutes",
            _positive_int(self.duration_minutes, "duration_minutes"),
        )


class Math6CanonicalBlueprintLike(Protocol):
    blueprint_code: str
    title: str
    question_count: int
    total_score: Decimal
    review_status: str
    locked: bool
    canonical_subject_code: str
    canonical_program_code: str
    canonical_topic_codes: tuple[str, ...]
    canonical_requirement_codes: tuple[str, ...]
    requirement_assignments: tuple[BlueprintRequirementAssignment, ...]
    matrix_sections: tuple[AssessmentProfileSectionOption, ...]
    matrix_cognitive_levels: tuple[CognitiveLevelOption, ...]
    matrix_cells: tuple[AssessmentMatrixCell, ...]


def build_math6_canonical_snapshot(
    *,
    blueprint: Math6CanonicalBlueprintLike,
    identity: Math6CanonicalSnapshotIdentity,
    topics: Sequence[AssessmentCurriculumTopic],
    requirements: Sequence[AssessmentLearningRequirement],
    question_type_names: Mapping[str, str],
    competencies_by_requirement: Mapping[
        str,
        Sequence[CanonicalRequirementCompetency],
    ] | None = None,
) -> dict[str, object]:
    """Build canonical snapshot schema 2 without persistence or export."""

    if blueprint.review_status != "APPROVED" or not blueprint.locked:
        raise Math6CanonicalSnapshotBridgeError(
            "canonical snapshot bridge requires an approved locked blueprint"
        )

    subject_code = _text(
        blueprint.canonical_subject_code,
        "canonical_subject_code",
    ).upper()
    program_code = _text(
        blueprint.canonical_program_code,
        "canonical_program_code",
    ).upper()

    topic_codes = tuple(blueprint.canonical_topic_codes)
    requirement_codes = tuple(blueprint.canonical_requirement_codes)
    assignments = tuple(blueprint.requirement_assignments)
    sections = tuple(blueprint.matrix_sections)
    cognitive_levels = tuple(blueprint.matrix_cognitive_levels)
    cells = tuple(blueprint.matrix_cells)

    if not topic_codes:
        raise Math6CanonicalSnapshotBridgeError(
            "canonical topics are required"
        )
    if not requirement_codes or not assignments:
        raise Math6CanonicalSnapshotBridgeError(
            "canonical requirements are required"
        )
    if not sections or not cognitive_levels or not cells:
        raise Math6CanonicalSnapshotBridgeError(
            "matrix authoring is required"
        )

    topic_by_code = {row.topic_code: row for row in topics}
    if set(topic_by_code) != set(topic_codes):
        raise Math6CanonicalSnapshotBridgeError(
            "topic catalog records must exactly match canonical topic codes"
        )

    for topic in topic_by_code.values():
        if int(topic.grade_level) != 6:
            raise Math6CanonicalSnapshotBridgeError(
                "canonical topics must target grade 6"
            )
        if str(topic.program_code).upper() != program_code:
            raise Math6CanonicalSnapshotBridgeError(
                "canonical topic program does not match blueprint"
            )

    requirement_by_code = {
        row.requirement_code: row
        for row in requirements
    }
    if set(requirement_by_code) != set(requirement_codes):
        raise Math6CanonicalSnapshotBridgeError(
            "requirement catalog records must exactly match canonical requirement codes"
        )

    assignment_by_code = {
        row.requirement_code: row
        for row in assignments
    }
    if set(assignment_by_code) != set(requirement_codes):
        raise Math6CanonicalSnapshotBridgeError(
            "requirement assignments must exactly match canonical requirement codes"
        )

    for requirement in requirement_by_code.values():
        if int(requirement.grade_level) != 6:
            raise Math6CanonicalSnapshotBridgeError(
                "canonical requirements must target grade 6"
            )
        if str(requirement.program_code).upper() != program_code:
            raise Math6CanonicalSnapshotBridgeError(
                "canonical requirement program does not match blueprint"
            )
        if requirement.topic_code not in topic_by_code:
            raise Math6CanonicalSnapshotBridgeError(
                "canonical requirement references an unselected topic"
            )

    section_by_code = {
        row.section_code: row
        for row in sections
    }
    level_by_code = {
        row.cognitive_level_code: row
        for row in cognitive_levels
    }

    normalized_question_type_names = {
        _text(code, "question_type_code").upper(): _text(
            name,
            "question_type_name",
        )
        for code, name in question_type_names.items()
    }
    required_question_types = {
        row.question_type_code
        for row in sections
    }
    if not required_question_types.issubset(
        normalized_question_type_names
    ):
        raise Math6CanonicalSnapshotBridgeError(
            "question type names must cover every matrix section"
        )

    competencies_source = competencies_by_requirement or {}
    extra_competency_codes = set(competencies_source) - set(requirement_codes)
    if extra_competency_codes:
        raise Math6CanonicalSnapshotBridgeError(
            "competency mapping contains an unknown requirement code"
        )

    snapshot_sections = [
        {
            "section_code": row.section_code,
            "section_name": row.section_name,
            "sequence_number": row.sequence_number,
        }
        for row in sorted(
            sections,
            key=lambda item: (
                item.sequence_number,
                item.section_code,
            ),
        )
    ]

    snapshot_cells: list[dict[str, object]] = []
    for cell in cells:
        try:
            section = section_by_code[cell.section_code]
        except KeyError as error:
            raise Math6CanonicalSnapshotBridgeError(
                "matrix cell references an unknown section"
            ) from error
        try:
            topic = topic_by_code[cell.topic_code]
        except KeyError as error:
            raise Math6CanonicalSnapshotBridgeError(
                "matrix cell references an unknown canonical topic"
            ) from error
        try:
            level = level_by_code[cell.cognitive_level_code]
        except KeyError as error:
            raise Math6CanonicalSnapshotBridgeError(
                "matrix cell references an unknown cognitive level"
            ) from error

        snapshot_cells.append(
            {
                "section_code": cell.section_code,
                "section_name": section.section_name,
                "topic_code": topic.topic_code,
                "topic_name": topic.topic_name,
                "domain_code": topic.domain_code,
                "topic_sequence_number": topic.sequence_number,
                "cognitive_level_code": cell.cognitive_level_code,
                "cognitive_level_name": level.cognitive_level_name,
                "cognitive_sequence_number": level.sequence_number,
                "question_type_code": section.question_type_code,
                "question_type_name": normalized_question_type_names[
                    section.question_type_code
                ],
                "question_count": cell.question_count,
                "response_count": cell.response_count,
                "target_score": _json_number(cell.target_score),
                "sequence_number": cell.sequence_number,
                "specification_note": cell.specification_note,
            }
        )

    snapshot_requirements: list[dict[str, object]] = []
    for requirement_code in sorted(
        requirement_codes,
        key=lambda code: (
            assignment_by_code[code].sequence_number,
            code,
        ),
    ):
        requirement = requirement_by_code[requirement_code]
        assignment = assignment_by_code[requirement_code]
        topic = topic_by_code[requirement.topic_code]
        competencies = tuple(
            competencies_source.get(requirement_code, ())
        )
        if any(
            not isinstance(row, CanonicalRequirementCompetency)
            for row in competencies
        ):
            raise Math6CanonicalSnapshotBridgeError(
                "competency mappings must use CanonicalRequirementCompetency"
            )

        snapshot_requirements.append(
            {
                "requirement_code": requirement.requirement_code,
                "requirement_text": requirement.requirement_text,
                "requirement_version_number": requirement.version_number,
                "source_locator": requirement.source_locator,
                "topic_code": topic.topic_code,
                "topic_name": topic.topic_name,
                "domain_code": topic.domain_code,
                "coverage_role": assignment.coverage_role,
                "target_question_count": assignment.target_question_count,
                "target_score": _json_number(
                    _score(
                        assignment.target_score,
                        "requirement target_score",
                    )
                ),
                "sequence_number": assignment.sequence_number,
                "specification_note": assignment.specification_note,
                "competencies": [
                    row.as_snapshot_record()
                    for row in competencies
                ],
            }
        )

    matrix_question_count = sum(
        int(row["question_count"])
        for row in snapshot_cells
    )
    matrix_score = sum(
        (
            Decimal(str(row["target_score"]))
            for row in snapshot_cells
        ),
        Decimal("0"),
    )
    if matrix_question_count != int(blueprint.question_count):
        raise Math6CanonicalSnapshotBridgeError(
            "matrix question count does not match blueprint"
        )
    if matrix_score != Decimal(str(blueprint.total_score)):
        raise Math6CanonicalSnapshotBridgeError(
            "matrix score does not match blueprint"
        )

    return {
        "snapshot_schema_version": 2,
        "publication": {
            "publication_id": identity.publication_id,
            "published_at": identity.published_at,
        },
        "exam": {
            "exam_version_id": identity.exam_version_id,
            "exam_title": identity.exam_title,
            "subject_code": subject_code,
            "grade_level": 6,
            "total_score": _json_number(
                Decimal(str(blueprint.total_score))
            ),
            "duration_minutes": identity.duration_minutes,
        },
        "blueprint": {
            "blueprint_version_id": identity.blueprint_version_id,
            "blueprint_code": blueprint.blueprint_code,
            "blueprint_name": blueprint.title,
            "program_code": program_code,
            "sections": snapshot_sections,
            "matrix_cells": snapshot_cells,
            "requirement_links": snapshot_requirements,
        },
        "questions": [],
    }
