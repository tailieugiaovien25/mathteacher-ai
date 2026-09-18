"""PPCT adapter for the generic source-to-canonical binding boundary.

PPCT is operational/secondary data. This adapter converts PPCT rows into the
stable, source-neutral CurriculumSourceItem contract. The canonical curriculum
and assessment domains must not read PPCTRow directly after this boundary.

Identity rules:
- source identity comes from explicit runtime context,
- external_item_key is the PPCT period inside that source version,
- lesson title is evidence/display metadata only,
- exact duplicate rows at one period collapse,
- conflicting rows at one period fail closed,
- no fuzzy matching and no canonical-ID inference occur here.
"""

from __future__ import annotations

from dataclasses import dataclass

from curriculum_v2.source_binding import (
    CurriculumSourceItem,
)
from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)


class PpctCurriculumSourceAdapterError(ValueError):
    """Raised when PPCT cannot be adapted deterministically."""


def _required_text(
    value: object,
    field_name: str,
) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise PpctCurriculumSourceAdapterError(
            f"{field_name} must not be empty"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class PpctSourceContext:
    """Explicit identity/evidence for one PPCT source snapshot."""

    source_id: str
    source_version: str
    academic_year: str
    subject_code: str
    grade_level: int
    source_location: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _required_text(
                self.source_id,
                "source_id",
            ),
        )
        object.__setattr__(
            self,
            "source_version",
            _required_text(
                self.source_version,
                "source_version",
            ),
        )
        object.__setattr__(
            self,
            "academic_year",
            _required_text(
                self.academic_year,
                "academic_year",
            ),
        )
        object.__setattr__(
            self,
            "subject_code",
            _required_text(
                self.subject_code,
                "subject_code",
            ).upper(),
        )

        if isinstance(self.grade_level, bool):
            raise PpctCurriculumSourceAdapterError(
                "grade_level must be an integer from 1 to 12"
            )

        try:
            grade_level = int(
                self.grade_level
            )
        except (TypeError, ValueError) as error:
            raise PpctCurriculumSourceAdapterError(
                "grade_level must be an integer from 1 to 12"
            ) from error

        if grade_level < 1 or grade_level > 12:
            raise PpctCurriculumSourceAdapterError(
                "grade_level must be an integer from 1 to 12"
            )

        object.__setattr__(
            self,
            "grade_level",
            grade_level,
        )

        if self.source_location is not None:
            source_location = str(
                self.source_location
            ).strip()
            object.__setattr__(
                self,
                "source_location",
                source_location or None,
            )


class PpctCurriculumSourceAdapter:
    """Convert PPCT rows into stable generic source items."""

    SOURCE_TYPE = "PPCT"

    def adapt(
        self,
        *,
        rows: tuple[PPCTRow, ...],
        context: PpctSourceContext,
    ) -> tuple[CurriculumSourceItem, ...]:
        if not isinstance(rows, tuple):
            raise TypeError(
                "rows must be a tuple"
            )

        if not isinstance(
            context,
            PpctSourceContext,
        ):
            raise TypeError(
                "context must be PpctSourceContext"
            )

        by_period: dict[int, PPCTRow] = {}

        for row in rows:
            if not isinstance(row, PPCTRow):
                raise TypeError(
                    "rows must contain PPCTRow values"
                )

            period = int(row.period)

            if period <= 0:
                raise PpctCurriculumSourceAdapterError(
                    "PPCT period must be greater than 0"
                )

            normalized = PPCTRow(
                subject_grade=_required_text(
                    row.subject_grade,
                    "subject_grade",
                ),
                period=period,
                lesson_name=_required_text(
                    row.lesson_name,
                    "lesson_name",
                ),
                sub_subject=(
                    str(row.sub_subject).strip()
                    if row.sub_subject is not None
                    and str(row.sub_subject).strip()
                    else None
                ),
            )

            existing = by_period.get(period)

            if existing is None:
                by_period[period] = normalized
                continue

            if self._same_row(
                existing,
                normalized,
            ):
                continue

            raise PpctCurriculumSourceAdapterError(
                "PPCT period is ambiguous within the "
                "same source version: "
                f"{period}"
            )

        return tuple(
            self._to_source_item(
                row=row,
                context=context,
            )
            for _, row in sorted(
                by_period.items(),
                key=lambda item: item[0],
            )
        )

    @staticmethod
    def _same_row(
        left: PPCTRow,
        right: PPCTRow,
    ) -> bool:
        return (
            left.subject_grade.strip()
            == right.subject_grade.strip()
            and left.period == right.period
            and left.lesson_name.strip()
            == right.lesson_name.strip()
            and (
                (left.sub_subject or "").strip()
                == (right.sub_subject or "").strip()
            )
        )

    @classmethod
    def _to_source_item(
        cls,
        *,
        row: PPCTRow,
        context: PpctSourceContext,
    ) -> CurriculumSourceItem:
        external_item_key = (
            f"PERIOD:{int(row.period):04d}"
        )

        source_location = (
            f"{context.source_location}"
            f"#period={int(row.period)}"
            if context.source_location
            else f"ppct:period={int(row.period)}"
        )

        return CurriculumSourceItem(
            source_type=cls.SOURCE_TYPE,
            source_id=context.source_id,
            source_version=context.source_version,
            academic_year=context.academic_year,
            subject_code=context.subject_code,
            grade_level=context.grade_level,
            external_item_key=external_item_key,
            sequence=int(row.period),
            title=row.lesson_name.strip(),
            source_location=source_location,
        )
