"""Deterministic question-slot planning for approved assessment blueprints."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from uuid import UUID


class AssessmentQuestionSlotPlanningError(ValueError):
    """Raised when blueprint requirements cannot be partitioned safely."""


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise AssessmentQuestionSlotPlanningError(
            f"{field_name} must not be blank"
        )
    return normalized


def _uuid(value: object, field_name: str) -> str:
    normalized = _text(value, field_name)
    try:
        return str(UUID(normalized))
    except ValueError as error:
        raise AssessmentQuestionSlotPlanningError(
            f"{field_name} must be a valid UUID"
        ) from error


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 1:
        raise AssessmentQuestionSlotPlanningError(
            f"{field_name} must be positive"
        )
    return value


def _nonnegative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise AssessmentQuestionSlotPlanningError(
            f"{field_name} must be non-negative"
        )
    return value


def _positive_decimal(value: object, field_name: str) -> Decimal:
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise AssessmentQuestionSlotPlanningError(
            f"{field_name} must be numeric"
        ) from error
    if not normalized.is_finite() or normalized <= 0:
        raise AssessmentQuestionSlotPlanningError(
            f"{field_name} must be positive"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class BlueprintQuestionSlotCell:
    blueprint_cell_id: str
    sequence_number: int
    section_code: str
    topic_code: str
    cognitive_level_code: str
    question_type_code: str
    question_count: int
    target_score: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "blueprint_cell_id",
            _uuid(self.blueprint_cell_id, "blueprint_cell_id"),
        )
        object.__setattr__(
            self,
            "sequence_number",
            _nonnegative_int(self.sequence_number, "sequence_number"),
        )
        for field_name in (
            "section_code",
            "topic_code",
            "cognitive_level_code",
            "question_type_code",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "question_count",
            _positive_int(self.question_count, "question_count"),
        )
        object.__setattr__(
            self,
            "target_score",
            _positive_decimal(self.target_score, "target_score"),
        )

    @property
    def score_per_question(self) -> Decimal:
        return self.target_score / self.question_count


@dataclass(frozen=True, slots=True)
class BlueprintQuestionSlotRequirement:
    requirement_code: str
    topic_code: str
    sequence_number: int
    target_question_count: int
    target_score: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requirement_code",
            _text(self.requirement_code, "requirement_code"),
        )
        object.__setattr__(
            self,
            "topic_code",
            _text(self.topic_code, "topic_code"),
        )
        object.__setattr__(
            self,
            "sequence_number",
            _nonnegative_int(self.sequence_number, "sequence_number"),
        )
        object.__setattr__(
            self,
            "target_question_count",
            _positive_int(
                self.target_question_count,
                "target_question_count",
            ),
        )
        object.__setattr__(
            self,
            "target_score",
            _positive_decimal(self.target_score, "target_score"),
        )

    @property
    def score_per_question(self) -> Decimal:
        return self.target_score / self.target_question_count


@dataclass(frozen=True, slots=True)
class BlueprintQuestionSlot:
    blueprint_version_id: str
    blueprint_cell_id: str
    requirement_code: str
    requirement_occurrence_number: int
    slot_number: int
    display_position: int
    section_code: str
    topic_code: str
    cognitive_level_code: str
    question_type_code: str
    target_score: Decimal


class AssessmentQuestionSlotPlanningService:
    """Partition approved blueprint requirements into immutable question slots."""

    SCORE_TOLERANCE = Decimal("0.0001")

    def plan(
        self,
        *,
        blueprint_version_id: str,
        cells: tuple[BlueprintQuestionSlotCell, ...],
        requirements: tuple[BlueprintQuestionSlotRequirement, ...],
    ) -> tuple[BlueprintQuestionSlot, ...]:
        blueprint_version_id = _uuid(
            blueprint_version_id,
            "blueprint_version_id",
        )
        cells = tuple(cells)
        requirements = tuple(requirements)

        if not cells:
            raise AssessmentQuestionSlotPlanningError(
                "cells must not be empty"
            )
        if not requirements:
            raise AssessmentQuestionSlotPlanningError(
                "requirements must not be empty"
            )
        if any(not isinstance(row, BlueprintQuestionSlotCell) for row in cells):
            raise TypeError("cells contains an invalid value")
        if any(
            not isinstance(row, BlueprintQuestionSlotRequirement)
            for row in requirements
        ):
            raise TypeError("requirements contains an invalid value")

        cell_ids = tuple(row.blueprint_cell_id for row in cells)
        if len(set(cell_ids)) != len(cell_ids):
            raise AssessmentQuestionSlotPlanningError(
                "blueprint_cell_id values must be unique"
            )

        requirement_codes = tuple(
            row.requirement_code for row in requirements
        )
        if len(set(requirement_codes)) != len(requirement_codes):
            raise AssessmentQuestionSlotPlanningError(
                "requirement_code values must be unique"
            )

        ordered_cells = tuple(
            sorted(
                cells,
                key=lambda row: (
                    row.sequence_number,
                    row.blueprint_cell_id,
                ),
            )
        )
        ordered_requirements = tuple(
            sorted(
                requirements,
                key=lambda row: (
                    row.sequence_number,
                    row.requirement_code,
                ),
            )
        )

        by_cell: dict[str, list[BlueprintQuestionSlotRequirement]] = {
            row.blueprint_cell_id: [] for row in ordered_cells
        }

        for requirement in ordered_requirements:
            candidate_cells = tuple(
                cell
                for cell in ordered_cells
                if cell.topic_code == requirement.topic_code
                and abs(
                    cell.score_per_question
                    - requirement.score_per_question
                )
                <= self.SCORE_TOLERANCE
            )
            if len(candidate_cells) != 1:
                raise AssessmentQuestionSlotPlanningError(
                    "each requirement must map to exactly one matrix cell "
                    "by topic and per-question score"
                )
            by_cell[candidate_cells[0].blueprint_cell_id].append(
                requirement
            )

        for cell in ordered_cells:
            mapped = tuple(by_cell[cell.blueprint_cell_id])
            mapped_question_count = sum(
                row.target_question_count for row in mapped
            )
            mapped_target_score = sum(
                (row.target_score for row in mapped),
                Decimal("0"),
            )
            if (
                mapped_question_count != cell.question_count
                or abs(mapped_target_score - cell.target_score)
                > self.SCORE_TOLERANCE
            ):
                raise AssessmentQuestionSlotPlanningError(
                    "requirements must exactly partition every matrix cell"
                )

        slots: list[BlueprintQuestionSlot] = []
        display_position = 0

        for cell in ordered_cells:
            slot_number = 0
            for requirement in by_cell[cell.blueprint_cell_id]:
                for occurrence in range(
                    1,
                    requirement.target_question_count + 1,
                ):
                    slot_number += 1
                    display_position += 1
                    slots.append(
                        BlueprintQuestionSlot(
                            blueprint_version_id=blueprint_version_id,
                            blueprint_cell_id=cell.blueprint_cell_id,
                            requirement_code=requirement.requirement_code,
                            requirement_occurrence_number=occurrence,
                            slot_number=slot_number,
                            display_position=display_position,
                            section_code=cell.section_code,
                            topic_code=cell.topic_code,
                            cognitive_level_code=cell.cognitive_level_code,
                            question_type_code=cell.question_type_code,
                            target_score=requirement.score_per_question,
                        )
                    )

        expected_count = sum(row.question_count for row in ordered_cells)
        if len(slots) != expected_count:
            raise AssessmentQuestionSlotPlanningError(
                "planned slot count does not match blueprint question count"
            )

        return tuple(slots)


__all__ = [
    "AssessmentQuestionSlotPlanningError",
    "AssessmentQuestionSlotPlanningService",
    "BlueprintQuestionSlot",
    "BlueprintQuestionSlotCell",
    "BlueprintQuestionSlotRequirement",
]
