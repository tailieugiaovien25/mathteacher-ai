"""Pure matrix-cell authoring contracts shared by assessment workflows."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Sequence


class AssessmentMatrixAuthoringError(ValueError):
    """Raised when a matrix profile or generated allocation is invalid."""


def _text(value: object, field: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise AssessmentMatrixAuthoringError(f"{field} is required")
    return normalized


def _decimal(value: object, field: str) -> Decimal:
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise AssessmentMatrixAuthoringError(
            f"{field} must be a valid number"
        ) from error
    if not normalized.is_finite():
        raise AssessmentMatrixAuthoringError(
            f"{field} must be a finite number"
        )
    return normalized


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise AssessmentMatrixAuthoringError(f"{field} must be positive")
    try:
        normalized = int(value)
    except (TypeError, ValueError) as error:
        raise AssessmentMatrixAuthoringError(
            f"{field} must be positive"
        ) from error
    if normalized < 1:
        raise AssessmentMatrixAuthoringError(
            f"{field} must be positive"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class AssessmentProfileSectionOption:
    section_code: str
    section_name: str
    question_type_code: str
    sequence_number: int
    question_count: int
    response_count: int
    section_score: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "section_code",
            _text(self.section_code, "section_code").upper(),
        )
        object.__setattr__(
            self, "section_name",
            _text(self.section_name, "section_name"),
        )
        object.__setattr__(
            self, "question_type_code",
            _text(self.question_type_code, "question_type_code").upper(),
        )
        object.__setattr__(
            self, "sequence_number",
            _positive_int(self.sequence_number, "sequence_number"),
        )
        object.__setattr__(
            self, "question_count",
            _positive_int(self.question_count, "question_count"),
        )
        object.__setattr__(
            self, "response_count",
            _positive_int(self.response_count, "response_count"),
        )
        score = _decimal(self.section_score, "section_score")
        if score <= 0:
            raise AssessmentMatrixAuthoringError(
                "section_score must be positive"
            )
        object.__setattr__(self, "section_score", score)

    @property
    def label(self) -> str:
        return f"{self.section_code} ? {self.section_name}"

    def as_snapshot_record(self) -> dict[str, object]:
        return {
            "section_code": self.section_code,
            "section_name": self.section_name,
            "question_type_code": self.question_type_code,
            "sequence_number": self.sequence_number,
            "question_count": self.question_count,
            "response_count": self.response_count,
            "section_score": str(self.section_score),
        }


@dataclass(frozen=True, slots=True)
class CognitiveLevelOption:
    cognitive_level_code: str
    cognitive_level_name: str
    sequence_number: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "cognitive_level_code",
            _text(
                self.cognitive_level_code,
                "cognitive_level_code",
            ).upper(),
        )
        object.__setattr__(
            self, "cognitive_level_name",
            _text(
                self.cognitive_level_name,
                "cognitive_level_name",
            ),
        )
        object.__setattr__(
            self, "sequence_number",
            _positive_int(self.sequence_number, "sequence_number"),
        )

    @property
    def label(self) -> str:
        return (
            f"{self.cognitive_level_code} ? "
            f"{self.cognitive_level_name}"
        )

    def as_snapshot_record(self) -> dict[str, object]:
        return {
            "cognitive_level_code": self.cognitive_level_code,
            "cognitive_level_name": self.cognitive_level_name,
            "sequence_number": self.sequence_number,
        }


@dataclass(frozen=True, slots=True)
class ProfileLevelAllocation:
    cognitive_level_code: str
    target_score: Decimal
    target_percentage: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "cognitive_level_code",
            _text(
                self.cognitive_level_code,
                "cognitive_level_code",
            ).upper(),
        )
        score = _decimal(self.target_score, "target_score")
        percentage = _decimal(
            self.target_percentage,
            "target_percentage",
        )
        if score <= 0:
            raise AssessmentMatrixAuthoringError(
                "target_score must be positive"
            )
        if percentage <= 0:
            raise AssessmentMatrixAuthoringError(
                "target_percentage must be positive"
            )
        object.__setattr__(self, "target_score", score)
        object.__setattr__(self, "target_percentage", percentage)

    def as_snapshot_record(self) -> dict[str, object]:
        return {
            "cognitive_level_code": self.cognitive_level_code,
            "target_score": str(self.target_score),
            "target_percentage": str(self.target_percentage),
        }


@dataclass(frozen=True, slots=True)
class AssessmentMatrixCell:
    section_code: str
    topic_code: str
    cognitive_level_code: str
    question_count: int
    response_count: int
    target_score: Decimal
    sequence_number: int
    specification_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "section_code",
            _text(self.section_code, "section_code").upper(),
        )
        object.__setattr__(
            self, "topic_code",
            _text(self.topic_code, "topic_code").upper(),
        )
        object.__setattr__(
            self, "cognitive_level_code",
            _text(
                self.cognitive_level_code,
                "cognitive_level_code",
            ).upper(),
        )
        object.__setattr__(
            self, "question_count",
            _positive_int(self.question_count, "question_count"),
        )
        object.__setattr__(
            self, "response_count",
            _positive_int(self.response_count, "response_count"),
        )
        score = _decimal(self.target_score, "target_score")
        if score <= 0:
            raise AssessmentMatrixAuthoringError(
                "target_score must be positive"
            )
        object.__setattr__(self, "target_score", score)
        object.__setattr__(
            self, "sequence_number",
            _positive_int(self.sequence_number, "sequence_number"),
        )
        object.__setattr__(
            self, "specification_note",
            str(self.specification_note or "").strip(),
        )

    def as_payload_record(self) -> dict[str, object]:
        return {
            "section_code": self.section_code,
            "topic_code": self.topic_code,
            "cognitive_level_code": self.cognitive_level_code,
            "question_count": self.question_count,
            "response_count": self.response_count,
            "target_score": str(self.target_score),
            "sequence_number": self.sequence_number,
            "specification_note": self.specification_note,
        }


def build_default_matrix_cells(
    *,
    sections: Sequence[AssessmentProfileSectionOption],
    topic_codes: Sequence[str],
    cognitive_levels: Sequence[CognitiveLevelOption],
    level_allocations: Sequence[ProfileLevelAllocation],
) -> tuple[AssessmentMatrixCell, ...]:
    section_rows = tuple(sections)
    level_rows = tuple(cognitive_levels)
    allocation_rows = tuple(level_allocations)
    topics = tuple(
        dict.fromkeys(
            _text(code, "topic_code").upper()
            for code in topic_codes
        )
    )
    if not section_rows:
        raise AssessmentMatrixAuthoringError(
            "at least one assessment section is required"
        )
    if not topics:
        raise AssessmentMatrixAuthoringError(
            "at least one topic_code is required"
        )
    if not level_rows:
        raise AssessmentMatrixAuthoringError(
            "at least one cognitive level is required"
        )
    if not allocation_rows:
        raise AssessmentMatrixAuthoringError(
            "at least one level allocation is required"
        )

    allocation_by_level = {
        item.cognitive_level_code: item.target_score
        for item in allocation_rows
    }
    ordered_targets: list[list[object]] = [
        [
            level.cognitive_level_code,
            allocation_by_level.get(
                level.cognitive_level_code,
                Decimal("0"),
            ),
        ]
        for level in level_rows
        if allocation_by_level.get(
            level.cognitive_level_code,
            Decimal("0"),
        ) > 0
    ]

    allocated: list[AssessmentMatrixCell] = []
    target_index = 0
    allocation_possible = bool(ordered_targets)

    for section in section_rows:
        remaining_score = section.section_score
        section_part = 0
        while remaining_score > 0 and target_index < len(ordered_targets):
            level_code = str(ordered_targets[target_index][0])
            level_remaining = Decimal(
                str(ordered_targets[target_index][1])
            )
            chunk_score = min(remaining_score, level_remaining)
            question_fraction = (
                Decimal(section.question_count)
                * chunk_score
                / section.section_score
            )
            response_fraction = (
                Decimal(section.response_count)
                * chunk_score
                / section.section_score
            )
            if (
                question_fraction
                != question_fraction.to_integral_value()
                or response_fraction
                != response_fraction.to_integral_value()
            ):
                allocation_possible = False
                break

            allocated.append(
                AssessmentMatrixCell(
                    section_code=section.section_code,
                    topic_code=topics[len(allocated) % len(topics)],
                    cognitive_level_code=level_code,
                    question_count=int(question_fraction),
                    response_count=int(response_fraction),
                    target_score=chunk_score,
                    sequence_number=(
                        section.sequence_number + section_part
                    ),
                )
            )
            section_part += 1
            remaining_score -= chunk_score
            ordered_targets[target_index][1] = (
                level_remaining - chunk_score
            )
            if Decimal(
                str(ordered_targets[target_index][1])
            ) == 0:
                target_index += 1

        if not allocation_possible or remaining_score != 0:
            allocation_possible = False
            break

    if (
        allocation_possible
        and all(
            Decimal(str(remaining)) == 0
            for _, remaining in ordered_targets
        )
    ):
        result = tuple(allocated)
    else:
        result = tuple(
            AssessmentMatrixCell(
                section_code=section.section_code,
                topic_code=topics[index % len(topics)],
                cognitive_level_code=(
                    level_rows[index % len(level_rows)].cognitive_level_code
                ),
                question_count=section.question_count,
                response_count=section.response_count,
                target_score=section.section_score,
                sequence_number=section.sequence_number,
            )
            for index, section in enumerate(section_rows)
        )

    validate_matrix_cells(
        cells=result,
        sections=section_rows,
        cognitive_levels=level_rows,
        level_allocations=allocation_rows,
    )
    return result


def validate_matrix_cells(
    *,
    cells: Sequence[AssessmentMatrixCell],
    sections: Sequence[AssessmentProfileSectionOption],
    cognitive_levels: Sequence[CognitiveLevelOption],
    level_allocations: Sequence[ProfileLevelAllocation],
) -> None:
    matrix_cells = tuple(cells)
    if not matrix_cells:
        raise AssessmentMatrixAuthoringError(
            "matrix must contain at least one cell"
        )

    section_by_code = {
        section.section_code: section
        for section in sections
    }
    level_codes = {
        level.cognitive_level_code
        for level in cognitive_levels
    }
    allocation_by_level = {
        item.cognitive_level_code: item
        for item in level_allocations
    }

    for cell in matrix_cells:
        if cell.section_code not in section_by_code:
            raise AssessmentMatrixAuthoringError(
                "matrix cell references an unknown section"
            )
        if cell.cognitive_level_code not in level_codes:
            raise AssessmentMatrixAuthoringError(
                "matrix cell references an unknown cognitive level"
            )

    for section_code, section in section_by_code.items():
        rows = tuple(
            cell for cell in matrix_cells
            if cell.section_code == section_code
        )
        if sum(
            cell.question_count for cell in rows
        ) != section.question_count:
            raise AssessmentMatrixAuthoringError(
                "matrix section question totals do not match profile"
            )
        if sum(
            cell.response_count for cell in rows
        ) != section.response_count:
            raise AssessmentMatrixAuthoringError(
                "matrix section response totals do not match profile"
            )
        if sum(
            (cell.target_score for cell in rows),
            Decimal("0"),
        ) != section.section_score:
            raise AssessmentMatrixAuthoringError(
                "matrix section score totals do not match profile"
            )

    for level_code, allocation in allocation_by_level.items():
        actual = sum(
            (
                cell.target_score
                for cell in matrix_cells
                if cell.cognitive_level_code == level_code
            ),
            Decimal("0"),
        )
        if actual != allocation.target_score:
            raise AssessmentMatrixAuthoringError(
                "matrix cognitive-level score totals do not match profile"
            )

    section_total = sum(
        (section.section_score for section in sections),
        Decimal("0"),
    )
    allocation_total = sum(
        (
            allocation.target_score
            for allocation in level_allocations
        ),
        Decimal("0"),
    )
    if section_total != allocation_total:
        raise AssessmentMatrixAuthoringError(
            "section and cognitive-level score totals must match"
        )


def matrix_cells_payload(
    cells: Iterable[AssessmentMatrixCell],
) -> tuple[dict[str, object], ...]:
    rows = tuple(cells)
    if not rows:
        raise AssessmentMatrixAuthoringError(
            "matrix must contain at least one cell"
        )
    return tuple(cell.as_payload_record() for cell in rows)
