from dataclasses import dataclass

from educational_planning_v2.builders import PlanItemDraft
from utils.lesson_key import build_lesson_key


@dataclass(frozen=True)
class PPCTRow:
    """Minimal PPCT source row required by educational planning."""

    subject_grade: str
    period: int
    lesson_name: str


class PPCTPlanItemAdapter:
    """Adapt PPCT source rows into educational-planning drafts.

    This adapter owns only source normalization and lesson grouping.

    Canonical curriculum-node IDs and YCCD IDs are intentionally not
    invented here. They must be supplied later by the canonical
    curriculum / YCCD enrichment layer.
    """

    def adapt(
        self,
        *,
        grade: int,
        rows: tuple[PPCTRow, ...],
    ) -> tuple[PlanItemDraft, ...]:
        if not isinstance(grade, int) or isinstance(grade, bool):
            raise TypeError("grade must be an int")

        if grade <= 0:
            raise ValueError("grade must be greater than 0")

        if not isinstance(rows, tuple):
            raise TypeError("rows must be a tuple")

        normalized_rows = tuple(
            self._validate_row(row)
            for row in rows
        )

        groups: list[dict[str, object]] = []

        for row in normalized_rows:
            lesson_key = build_lesson_key(
                grade,
                row.subject_grade,
                row.lesson_name,
                row.period,
            )

            if not lesson_key:
                raise ValueError(
                    "could not build lesson_key for PPCT row: "
                    f"{row!r}"
                )

            if (
                groups
                and groups[-1]["lesson_key"] == lesson_key
            ):
                groups[-1]["periods"] = (
                    int(groups[-1]["periods"]) + 1
                )
                continue

            groups.append(
                {
                    "lesson_key": lesson_key,
                    "title": row.lesson_name,
                    "periods": 1,
                }
            )

        return tuple(
            PlanItemDraft(
                title=str(group["title"]),
                periods=int(group["periods"]),
            )
            for group in groups
        )

    @staticmethod
    def _validate_row(row: PPCTRow) -> PPCTRow:
        if not isinstance(row, PPCTRow):
            raise TypeError(
                "all rows must be PPCTRow instances"
            )

        if not isinstance(row.subject_grade, str):
            raise TypeError(
                "subject_grade must be a string"
            )

        if not isinstance(row.lesson_name, str):
            raise TypeError(
                "lesson_name must be a string"
            )

        if not isinstance(row.period, int) or isinstance(
            row.period,
            bool,
        ):
            raise TypeError(
                "period must be an int"
            )

        subject_grade = row.subject_grade.strip()
        lesson_name = row.lesson_name.strip()

        if not subject_grade:
            raise ValueError(
                "subject_grade must not be empty"
            )

        if not lesson_name:
            raise ValueError(
                "lesson_name must not be empty"
            )

        if row.period <= 0:
            raise ValueError(
                "period must be greater than 0"
            )

        return PPCTRow(
            subject_grade=subject_grade,
            period=row.period,
            lesson_name=lesson_name,
        )
