"""Canonical, template-independent assessment document model."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID


class CanonicalAssessmentDocumentError(ValueError):
    """Raised when immutable assessment payloads are inconsistent."""


def _mapping(
    value: object,
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CanonicalAssessmentDocumentError(
            f"{field_name} must be an object"
        )
    return dict(value)


def _sequence(
    value: object,
    field_name: str,
) -> list[object]:
    if not isinstance(value, list):
        raise CanonicalAssessmentDocumentError(
            f"{field_name} must be an array"
        )
    return list(value)


def _required_text(
    value: object,
    field_name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CanonicalAssessmentDocumentError(
            f"{field_name} is required"
        )
    return value.strip()


def _required_uuid(
    value: object,
    field_name: str,
) -> str:
    text = _required_text(value, field_name)
    try:
        return str(UUID(text))
    except ValueError as error:
        raise CanonicalAssessmentDocumentError(
            f"{field_name} must be a valid UUID"
        ) from error


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType(
            {
                str(key): _freeze(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze(item)
            for item in value
        )

    return value


@dataclass(frozen=True, slots=True)
class CanonicalAssessmentDocument:
    schema_version: int
    metadata: Mapping[str, object]
    matrix: tuple[Mapping[str, object], ...]
    specification: tuple[Mapping[str, object], ...]
    questions: tuple[Mapping[str, object], ...]
    answer_key: tuple[Mapping[str, object], ...]
    scoring_guide: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise CanonicalAssessmentDocumentError(
                "unsupported canonical document schema"
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze(dict(self.metadata)),
        )

        for field_name in (
            "matrix",
            "specification",
            "questions",
            "answer_key",
            "scoring_guide",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, tuple):
                raise CanonicalAssessmentDocumentError(
                    f"{field_name} must be a tuple"
                )

            object.__setattr__(
                self,
                field_name,
                tuple(
                    _freeze(dict(item))
                    for item in value
                ),
            )


class CanonicalAssessmentDocumentBuilder:
    """Build one stable document model from immutable database payloads."""

    SNAPSHOT_SCHEMA_VERSION = 2
    CANONICAL_SCHEMA_VERSION = 1

    def build(
        self,
        *,
        snapshot_document: dict[str, object],
        student_exam_payload: dict[str, object],
        answer_key_payload: dict[str, object],
        scoring_guide_payload: dict[str, object],
    ) -> CanonicalAssessmentDocument:
        snapshot = _mapping(
            snapshot_document,
            "snapshot_document",
        )

        if snapshot.get("snapshot_schema_version") != (
            self.SNAPSHOT_SCHEMA_VERSION
        ):
            raise CanonicalAssessmentDocumentError(
                "snapshot schema 2 is required"
            )

        publication = _mapping(
            snapshot.get("publication"),
            "snapshot.publication",
        )
        exam = _mapping(
            snapshot.get("exam"),
            "snapshot.exam",
        )
        blueprint = _mapping(
            snapshot.get("blueprint"),
            "snapshot.blueprint",
        )

        student = self._package(
            student_exam_payload,
            expected_type="STUDENT_EXAM",
        )
        answers = self._package(
            answer_key_payload,
            expected_type="ANSWER_KEY",
        )
        scoring = self._package(
            scoring_guide_payload,
            expected_type="SCORING_GUIDE",
        )

        snapshot_exam_version_id = _required_uuid(
            exam.get("exam_version_id"),
            "snapshot.exam.exam_version_id",
        )

        for package_name, package in (
            ("student", student),
            ("answer", answers),
            ("scoring", scoring),
        ):
            package_exam = _mapping(
                package.get("exam"),
                f"{package_name}.exam",
            )
            package_exam_version_id = _required_uuid(
                package_exam.get("exam_version_id"),
                f"{package_name}.exam.exam_version_id",
            )

            if (
                package_exam_version_id
                != snapshot_exam_version_id
            ):
                raise CanonicalAssessmentDocumentError(
                    "package exam version does not match snapshot"
                )

        variants = (
            _mapping(student.get("variant"), "student.variant"),
            _mapping(answers.get("variant"), "answer.variant"),
            _mapping(scoring.get("variant"), "scoring.variant"),
        )

        variant_ids = tuple(
            _required_uuid(
                variant.get("variant_id"),
                "variant.variant_id",
            )
            for variant in variants
        )
        variant_codes = tuple(
            _required_text(
                variant.get("variant_code"),
                "variant.variant_code",
            )
            for variant in variants
        )

        if len(set(variant_ids)) != 1:
            raise CanonicalAssessmentDocumentError(
                "payloads belong to different variants"
            )

        if len(set(variant_codes)) != 1:
            raise CanonicalAssessmentDocumentError(
                "payload variant codes do not match"
            )

        sections = self._object_array(
            blueprint.get("sections"),
            "blueprint.sections",
        )
        cells = self._object_array(
            blueprint.get("matrix_cells"),
            "blueprint.matrix_cells",
        )
        requirements = self._object_array(
            blueprint.get("requirement_links"),
            "blueprint.requirement_links",
        )

        matrix = self._build_matrix(
            sections=sections,
            cells=cells,
        )
        specification = self._build_specification(
            requirements=requirements,
            cells=cells,
        )

        questions = tuple(
            self._ordered_items(
                self._object_array(
                    student.get("questions"),
                    "student.questions",
                ),
                key="display_number",
            )
        )
        answer_key = tuple(
            self._ordered_items(
                self._object_array(
                    answers.get("answers"),
                    "answer.answers",
                ),
                key="display_number",
            )
        )
        scoring_guide = tuple(
            self._ordered_items(
                self._object_array(
                    scoring.get("scoring_items"),
                    "scoring.scoring_items",
                ),
                key="display_number",
            )
        )

        question_numbers = tuple(
            item.get("display_number")
            for item in questions
        )
        answer_numbers = tuple(
            item.get("display_number")
            for item in answer_key
        )
        scoring_numbers = tuple(
            item.get("display_number")
            for item in scoring_guide
        )

        if not (
            question_numbers
            == answer_numbers
            == scoring_numbers
        ):
            raise CanonicalAssessmentDocumentError(
                "question, answer, and scoring sequences differ"
            )

        metadata = {
            "canonical_schema_version": (
                self.CANONICAL_SCHEMA_VERSION
            ),
            "snapshot_schema_version": (
                self.SNAPSHOT_SCHEMA_VERSION
            ),
            "publication": publication,
            "exam": exam,
            "blueprint": {
                key: value
                for key, value in blueprint.items()
                if key not in (
                    "sections",
                    "matrix_cells",
                    "requirement_links",
                )
            },
            "variant": variants[0],
            "totals": {
                "matrix_cell_count": len(cells),
                "requirement_count": len(requirements),
                "question_count": len(questions),
                "total_score": exam.get("total_score"),
            },
        }

        return CanonicalAssessmentDocument(
            schema_version=self.CANONICAL_SCHEMA_VERSION,
            metadata=metadata,
            matrix=matrix,
            specification=specification,
            questions=questions,
            answer_key=answer_key,
            scoring_guide=scoring_guide,
        )

    def _package(
        self,
        value: object,
        *,
        expected_type: str,
    ) -> dict[str, Any]:
        package = _mapping(
            value,
            f"{expected_type.lower()}_payload",
        )

        if package.get("package_schema_version") != 1:
            raise CanonicalAssessmentDocumentError(
                "unsupported package schema"
            )

        if package.get("package_type") != expected_type:
            raise CanonicalAssessmentDocumentError(
                f"{expected_type} payload is required"
            )

        return package

    def _object_array(
        self,
        value: object,
        field_name: str,
    ) -> list[dict[str, Any]]:
        items = _sequence(value, field_name)
        return [
            _mapping(
                item,
                f"{field_name}[{index}]",
            )
            for index, item in enumerate(items)
        ]

    def _ordered_items(
        self,
        items: list[dict[str, Any]],
        *,
        key: str,
    ) -> list[dict[str, Any]]:
        if any(
            not isinstance(item.get(key), int)
            for item in items
        ):
            raise CanonicalAssessmentDocumentError(
                f"{key} must be an integer"
            )

        ordered = sorted(
            items,
            key=lambda item: item[key],
        )

        values = tuple(
            item[key]
            for item in ordered
        )

        if len(set(values)) != len(values):
            raise CanonicalAssessmentDocumentError(
                f"{key} values must be unique"
            )

        return ordered

    def _build_matrix(
        self,
        *,
        sections: list[dict[str, Any]],
        cells: list[dict[str, Any]],
    ) -> tuple[Mapping[str, object], ...]:
        section_order = {
            section.get("section_code"): section.get(
                "sequence_number",
                0,
            )
            for section in sections
        }

        ordered_cells = sorted(
            cells,
            key=lambda cell: (
                section_order.get(
                    cell.get("section_code"),
                    0,
                ),
                cell.get("topic_sequence_number", 0),
                cell.get(
                    "cognitive_sequence_number",
                    0,
                ),
                cell.get("sequence_number", 0),
            ),
        )

        return tuple(
            {
                "section_code": cell.get("section_code"),
                "section_name": cell.get("section_name"),
                "topic_code": cell.get("topic_code"),
                "topic_name": cell.get("topic_name"),
                "domain_code": cell.get("domain_code"),
                "cognitive_level_code": cell.get(
                    "cognitive_level_code"
                ),
                "cognitive_level_name": cell.get(
                    "cognitive_level_name"
                ),
                "question_type_code": cell.get(
                    "question_type_code"
                ),
                "question_type_name": cell.get(
                    "question_type_name"
                ),
                "question_count": cell.get("question_count"),
                "response_count": cell.get("response_count"),
                "target_score": cell.get("target_score"),
                "specification_note": cell.get(
                    "specification_note"
                ),
            }
            for cell in ordered_cells
        )

    def _build_specification(
        self,
        *,
        requirements: list[dict[str, Any]],
        cells: list[dict[str, Any]],
    ) -> tuple[Mapping[str, object], ...]:
        cells_by_topic: dict[
            object,
            list[dict[str, Any]],
        ] = {}

        for cell in cells:
            cells_by_topic.setdefault(
                cell.get("topic_code"),
                [],
            ).append(cell)

        ordered_requirements = sorted(
            requirements,
            key=lambda requirement: (
                requirement.get("sequence_number", 0),
                str(requirement.get("requirement_code", "")),
            ),
        )

        return tuple(
            {
                "requirement_code": requirement.get(
                    "requirement_code"
                ),
                "requirement_text": requirement.get(
                    "requirement_text"
                ),
                "requirement_version_number": requirement.get(
                    "requirement_version_number"
                ),
                "source_locator": requirement.get(
                    "source_locator"
                ),
                "topic_code": requirement.get("topic_code"),
                "topic_name": requirement.get("topic_name"),
                "domain_code": requirement.get("domain_code"),
                "coverage_role": requirement.get(
                    "coverage_role"
                ),
                "target_question_count": requirement.get(
                    "target_question_count"
                ),
                "target_score": requirement.get(
                    "target_score"
                ),
                "specification_note": requirement.get(
                    "specification_note"
                ),
                "competencies": requirement.get(
                    "competencies",
                    [],
                ),
                "allocation_scope": "TOPIC",
                "topic_matrix_allocations": tuple(
                    {
                        "section_code": cell.get(
                            "section_code"
                        ),
                        "cognitive_level_code": cell.get(
                            "cognitive_level_code"
                        ),
                        "cognitive_level_name": cell.get(
                            "cognitive_level_name"
                        ),
                        "question_type_code": cell.get(
                            "question_type_code"
                        ),
                        "question_count": cell.get(
                            "question_count"
                        ),
                        "response_count": cell.get(
                            "response_count"
                        ),
                        "target_score": cell.get(
                            "target_score"
                        ),
                    }
                    for cell in cells_by_topic.get(
                        requirement.get("topic_code"),
                        [],
                    )
                ),
            }
            for requirement in ordered_requirements
        )
