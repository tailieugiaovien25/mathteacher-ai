from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)


@dataclass(frozen=True)
class PPCTScopeOption:
    subject_grade: str
    sub_subject: str | None = None

    @property
    def key(
        self,
    ) -> tuple[str, str | None]:
        return (
            self.subject_grade,
            self.sub_subject,
        )

    @property
    def label(
        self,
    ) -> str:
        if self.sub_subject:
            return (
                self.subject_grade
                + " | "
                + self.sub_subject
            )

        return self.subject_grade


class PPCTScopeCatalog:
    """
    Build selectable PPCT scopes from canonical PPCT rows.

    Contains no subject, grade, textbook, storage, or UI rules.
    """

    def build_options(
        self,
        *,
        rows: tuple[PPCTRow, ...],
    ) -> tuple[PPCTScopeOption, ...]:
        if not isinstance(
            rows,
            tuple,
        ):
            raise TypeError(
                "rows must be a tuple"
            )

        options = {}

        for row in rows:
            if not isinstance(
                row,
                PPCTRow,
            ):
                raise TypeError(
                    "rows contain invalid value"
                )

            subject_grade = (
                row.subject_grade.strip()
            )

            sub_subject = (
                row.sub_subject.strip()
                if row.sub_subject is not None
                and row.sub_subject.strip()
                else None
            )

            option = PPCTScopeOption(
                subject_grade=subject_grade,
                sub_subject=sub_subject,
            )

            options[
                option.key
            ] = option

        return tuple(
            sorted(
                options.values(),
                key=lambda item: (
                    item.subject_grade,
                    item.sub_subject or "",
                ),
            )
        )
