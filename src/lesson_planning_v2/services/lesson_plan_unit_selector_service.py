from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode,
)


@dataclass(frozen=True)
class LessonPlanUnitTeachingDate:
    teaching_date: date
    class_id: str


@dataclass(frozen=True)
class LessonPlanUnit:
    unit_id: str
    mode: LessonPlanSelectionMode
    title: str

    curriculum_periods: tuple[int, ...]
    class_ids: tuple[str, ...]
    teaching_dates: tuple[
        LessonPlanUnitTeachingDate,
        ...
    ]

    row_indices: tuple[int, ...]

    @property
    def total_periods(self) -> int:
        return len(
            self.curriculum_periods
        )

    @property
    def representative_index(self) -> int:
        if not self.row_indices:
            raise ValueError(
                "lesson plan unit has no source row"
            )

        return self.row_indices[0]

    @property
    def period_text(self) -> str:
        return " + ".join(
            str(value)
            for value
            in self.curriculum_periods
        )

    @property
    def selection_label(self) -> str:
        if (
            self.mode
            is LessonPlanSelectionMode.PERIOD
        ):
            return (
                f"Tiết {self.period_text} - "
                f"{self.title}"
            )

        if (
            self.mode
            is LessonPlanSelectionMode.TOPIC
        ):
            return (
                f"Chủ đề: {self.title} "
                f"(Tiết {self.period_text})"
            )

        return (
            f"{self.title} "
            f"(Tiết {self.period_text})"
        )


class LessonPlanUnitSelectorService:
    """
    Build lesson-plan working units from schedule rows.

    The selector is deliberately independent from:
    - Streamlit
    - Supabase
    - Excel layout
    - subject-specific rules

    Subject/template configuration chooses the default mode.
    """

    def build_units(
        self,
        *,
        rows: Iterable[object],
        mode: LessonPlanSelectionMode,
    ) -> tuple[
        LessonPlanUnit,
        ...
    ]:
        source_rows = tuple(rows)

        if mode is LessonPlanSelectionMode.PERIOD:
            return self._build_period_units(
                source_rows
            )

        if mode is LessonPlanSelectionMode.TOPIC:
            return self._build_topic_units(
                source_rows
            )

        if (
            mode
            is LessonPlanSelectionMode.WEEK_SUBJECT
        ):
            return self._build_week_subject_units(
                source_rows
            )

        return self._build_lesson_units(
            source_rows
        )

    def available_modes(
        self,
        *,
        rows: Iterable[object],
    ) -> tuple[
        LessonPlanSelectionMode,
        ...
    ]:
        rows = tuple(rows)

        result = [
            LessonPlanSelectionMode.LESSON,
            LessonPlanSelectionMode.PERIOD,
        ]

        if any(
            self._topic_identity(row)[0]
            for row in rows
        ):
            result.append(
                LessonPlanSelectionMode.TOPIC
            )

        if any(
            self._subject_ref(row)
            for row in rows
        ):
            result.append(
                LessonPlanSelectionMode
                .WEEK_SUBJECT
            )

        return tuple(result)

    def _build_lesson_units(
        self,
        rows: tuple[object, ...],
    ) -> tuple[
        LessonPlanUnit,
        ...
    ]:
        grouped = {}

        for index, row in enumerate(rows):
            lesson_id = str(
                getattr(
                    row,
                    "lesson_id",
                    "",
                )
                or ""
            ).strip()

            title = str(
                getattr(
                    row,
                    "lesson_title",
                    "",
                )
                or ""
            ).strip()

            if not title:
                continue

            # Transitional compatibility:
            # when current schedule view does not expose
            # lesson_id yet, title is used only as UI grouping
            # identity. Canonical lesson_id must still come
            # from PPCT when available.
            identity = (
                lesson_id
                if lesson_id
                else "title:" + title.casefold()
            )

            self._append(
                grouped=grouped,
                identity=identity,
                title=title,
                index=index,
                row=row,
            )

        return self._finish(
            grouped=grouped,
            mode=LessonPlanSelectionMode.LESSON,
        )

    def _build_period_units(
        self,
        rows: tuple[object, ...],
    ) -> tuple[
        LessonPlanUnit,
        ...
    ]:
        grouped = {}

        for index, row in enumerate(rows):
            period = self._period(row)

            if period is None:
                continue

            title = str(
                getattr(
                    row,
                    "lesson_title",
                    "",
                )
                or ""
            ).strip()

            subject_ref = self._subject_ref(row)
            component_ref = str(
                getattr(row, "component_ref", "") or ""
            ).strip()
            # V58-C3D3: PERIOD identity is the canonical PPCT occurrence
            # inside the already-resolved subject/component/grade scope.
            # Runtime lesson_id may be class-specific/generated, so it must
            # not split one PPCT period into duplicate selector options.
            identity = ":".join(
                (
                    "period",
                    subject_ref,
                    component_ref,
                    str(period),
                )
            )
            self._append(
                grouped=grouped,
                identity=identity,
                title=title or f"Tiết {period}",
                index=index,
                row=row,
            )

        return self._finish(
            grouped=grouped,
            mode=LessonPlanSelectionMode.PERIOD,
        )

    def _build_week_subject_units(
        self,
        rows: tuple[object, ...],
    ) -> tuple[
        LessonPlanUnit,
        ...
    ]:
        grouped = {}

        for index, row in enumerate(rows):
            subject_ref = self._subject_ref(
                row
            )

            if not subject_ref:
                continue

            title = self._subject_title(
                row=row,
                subject_ref=subject_ref,
            )

            self._append(
                grouped=grouped,
                identity=(
                    "week_subject:"
                    + subject_ref
                ),
                title=title,
                index=index,
                row=row,
            )

        return self._finish(
            grouped=grouped,
            mode=(
                LessonPlanSelectionMode
                .WEEK_SUBJECT
            ),
        )

    @staticmethod
    def _subject_ref(
        row: object,
    ) -> str:
        return str(
            getattr(
                row,
                "subject_ref",
                "",
            )
            or ""
        ).strip()

    @staticmethod
    def _subject_title(
        *,
        row: object,
        subject_ref: str,
    ) -> str:
        for field_name in (
            "subject_name",
            "subject_title",
        ):
            value = str(
                getattr(
                    row,
                    field_name,
                    "",
                )
                or ""
            ).strip()

            if value:
                return value

        return subject_ref

    def _build_topic_units(
        self,
        rows: tuple[object, ...],
    ) -> tuple[
        LessonPlanUnit,
        ...
    ]:
        grouped = {}

        for index, row in enumerate(rows):
            topic_id, topic_title = (
                self._topic_identity(
                    row
                )
            )

            if not topic_id:
                continue

            self._append(
                grouped=grouped,
                identity=topic_id,
                title=topic_title,
                index=index,
                row=row,
            )

        return self._finish(
            grouped=grouped,
            mode=LessonPlanSelectionMode.TOPIC,
        )

    @staticmethod
    def _topic_identity(
        row: object,
    ) -> tuple[str, str]:
        topic_id = str(
            getattr(
                row,
                "topic_id",
                "",
            )
            or ""
        ).strip()

        topic_title = str(
            getattr(
                row,
                "topic_title",
                "",
            )
            or ""
        ).strip()

        if not topic_id and topic_title:
            topic_id = (
                "topic:"
                + topic_title.casefold()
            )

        return (
            topic_id,
            topic_title,
        )

    @staticmethod
    def _period(
        row: object,
    ) -> int | None:
        value = getattr(
            row,
            "curriculum_period",
            None,
        )

        if value is None:
            return None

        return int(value)

    @staticmethod
    def _class_id(
        row: object,
    ) -> str:
        return str(
            getattr(
                row,
                "class_id",
                "",
            )
            or ""
        ).strip()

    def _append(
        self,
        *,
        grouped,
        identity: str,
        title: str,
        index: int,
        row: object,
    ) -> None:
        item = grouped.setdefault(
            identity,
            {
                "title": title,
                "periods": set(),
                "classes": set(),
                "dates": set(),
                "indices": [],
            },
        )

        period = self._period(row)

        if period is not None:
            item["periods"].add(
                period
            )

        class_id = self._class_id(
            row
        )

        if class_id:
            item["classes"].add(
                class_id
            )

        teaching_date = getattr(
            row,
            "teaching_date",
            None,
        )

        if (
            teaching_date is not None
            and class_id
        ):
            item["dates"].add(
                (
                    teaching_date,
                    class_id,
                )
            )

        item["indices"].append(
            index
        )

    @staticmethod
    def _finish(
        *,
        grouped,
        mode: LessonPlanSelectionMode,
    ) -> tuple[
        LessonPlanUnit,
        ...
    ]:
        result = []

        for identity, item in grouped.items():
            periods = tuple(
                sorted(
                    item["periods"]
                )
            )

            if not periods:
                continue

            dates = tuple(
                LessonPlanUnitTeachingDate(
                    teaching_date=value[0],
                    class_id=value[1],
                )
                for value in sorted(
                    item["dates"],
                    key=lambda value: (
                        value[0],
                        value[1],
                    ),
                )
            )

            result.append(
                LessonPlanUnit(
                    unit_id=identity,
                    mode=mode,
                    title=item["title"],
                    curriculum_periods=(
                        periods
                    ),
                    class_ids=tuple(
                        sorted(
                            item["classes"]
                        )
                    ),
                    teaching_dates=dates,
                    row_indices=tuple(
                        item["indices"]
                    ),
                )
            )

        return tuple(
            sorted(
                result,
                key=lambda unit: (
                    unit.curriculum_periods[0],
                    unit.title,
                ),
            )
        )
