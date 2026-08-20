from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlot,
    TeacherTimetableSlotStatus,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.models.weekly_teaching_schedule import (
    CurriculumPeriod,
    TimetableSlot,
)


@dataclass(frozen=True)
class WeeklyScheduleInputBuilder:
    """
    Convert persisted teacher-planning domain models into the
    canonical input required by WeeklyTeachingScheduleService.

    The builder is deliberately storage-neutral. It knows nothing
    about Supabase, SQL tables, workbooks, or Streamlit.
    """

    def build_timetable_slots(
        self,
        *,
        teacher_id: str,
        timetable_slots: tuple[
            TeacherTimetableSlot,
            ...,
        ],
        assignments: tuple[
            TeachingAssignment,
            ...,
        ],
    ) -> tuple[TimetableSlot, ...]:
        teacher_id = self._required_text(
            teacher_id,
            "teacher_id",
        )

        if not isinstance(
            timetable_slots,
            tuple,
        ):
            raise TypeError(
                "timetable_slots must be a tuple"
            )

        if not isinstance(
            assignments,
            tuple,
        ):
            raise TypeError(
                "assignments must be a tuple"
            )

        assignment_index = (
            self._build_assignment_index(
                teacher_id=teacher_id,
                assignments=assignments,
            )
        )

        result = []

        for slot in timetable_slots:
            if not isinstance(
                slot,
                TeacherTimetableSlot,
            ):
                raise TypeError(
                    "all timetable_slots must be "
                    "TeacherTimetableSlot instances"
                )

            if (
                slot.owner_id
                != teacher_id
            ):
                continue

            if (
                slot.status
                is not TeacherTimetableSlotStatus.ACTIVE
            ):
                continue

            assignment = assignment_index.get(
                slot.assignment_id
            )

            if assignment is None:
                raise ValueError(
                    "active timetable slot references "
                    "missing active teaching assignment: "
                    f"{slot.assignment_id}"
                )

            result.append(
                TimetableSlot(
                    teacher_id=teacher_id,
                    class_id=assignment.class_id,
                    subject_ref=(
                        assignment.subject_ref
                        or ""
                    ),
                    component_ref=(
                        assignment.component_ref
                    ),
                    weekday=slot.weekday,
                    timetable_period=slot.period,
                    session=slot.session,
                    effective_from=(
                        slot.effective_from
                    ),
                    effective_to=(
                        slot.effective_to
                    ),
                )
            )

        return tuple(
            sorted(
                result,
                key=lambda item: (
                    item.weekday,
                    item.timetable_period,
                    item.class_id,
                    item.subject_ref,
                    item.component_ref or "",
                ),
            )
        )

    def build_curriculum_periods(
        self,
        *,
        assignment: TeachingAssignment,
        ppct_rows: tuple[PPCTRow, ...],
    ) -> tuple[CurriculumPeriod, ...]:
        if not isinstance(
            assignment,
            TeachingAssignment,
        ):
            raise TypeError(
                "assignment must be TeachingAssignment"
            )

        if (
            assignment.role
            is not TeachingAssignmentRole.TEACHING
        ):
            raise ValueError(
                "assignment must have TEACHING role"
            )

        if (
            assignment.status
            is not TeachingAssignmentStatus.ACTIVE
        ):
            raise ValueError(
                "assignment must be ACTIVE"
            )

        if assignment.subject_ref is None:
            raise ValueError(
                "teaching assignment requires subject_ref"
            )

        if not isinstance(
            ppct_rows,
            tuple,
        ):
            raise TypeError(
                "ppct_rows must be a tuple"
            )

        ordered_rows = tuple(
            sorted(
                ppct_rows,
                key=lambda item: item.period,
            )
        )

        for row in ordered_rows:
            if not isinstance(
                row,
                PPCTRow,
            ):
                raise TypeError(
                    "all ppct_rows must be PPCTRow instances"
                )

        seen_periods = set()
        lesson_groups = self._lesson_groups(
            ordered_rows
        )

        result = []

        for row in ordered_rows:
            if row.period in seen_periods:
                raise ValueError(
                    "duplicate PPCT period: "
                    f"{row.period}"
                )

            seen_periods.add(
                row.period
            )

            group_key = self._lesson_group_key(
                row
            )

            group_periods = lesson_groups[
                group_key
            ]

            period_in_lesson = (
                group_periods.index(
                    row.period
                )
                + 1
            )

            result.append(
                CurriculumPeriod(
                    class_id=assignment.class_id,
                    subject_ref=assignment.subject_ref,
                    component_ref=(
                        assignment.component_ref
                    ),
                    period_number=row.period,
                    lesson_id=self._lesson_id(
                        assignment=assignment,
                        row=row,
                    ),
                    lesson_title=row.lesson_name,
                    period_in_lesson=(
                        period_in_lesson
                    ),
                    total_lesson_periods=len(
                        group_periods
                    ),
                )
            )

        return tuple(result)

    @classmethod
    def _lesson_groups(
        cls,
        rows: tuple[PPCTRow, ...],
    ) -> dict[
        tuple[str, str | None, str],
        tuple[int, ...],
    ]:
        groups: dict[
            tuple[str, str | None, str],
            list[int],
        ] = {}

        for row in rows:
            key = cls._lesson_group_key(
                row
            )

            groups.setdefault(
                key,
                [],
            ).append(
                row.period
            )

        return {
            key: tuple(
                sorted(periods)
            )
            for key, periods
            in groups.items()
        }

    @staticmethod
    def _lesson_group_key(
        row: PPCTRow,
    ) -> tuple[str, str | None, str]:
        return (
            row.subject_grade.strip(),
            (
                row.sub_subject.strip()
                if row.sub_subject is not None
                else None
            ),
            row.lesson_name.strip(),
        )

    @staticmethod
    def _lesson_id(
        *,
        assignment: TeachingAssignment,
        row: PPCTRow,
    ) -> str:
        identity = "|".join(
            (
                assignment.class_id,
                assignment.subject_ref or "",
                assignment.component_ref or "",
                row.subject_grade.strip(),
                (
                    row.sub_subject.strip()
                    if row.sub_subject is not None
                    else ""
                ),
                row.lesson_name.strip(),
            )
        )

        digest = sha256(
            identity.encode("utf-8")
        ).hexdigest()[:20]

        return (
            "ppct-lesson-"
            + digest
        )

    @staticmethod
    def _build_assignment_index(
        *,
        teacher_id: str,
        assignments: tuple[
            TeachingAssignment,
            ...,
        ],
    ) -> dict[str, TeachingAssignment]:
        result = {}

        for assignment in assignments:
            if not isinstance(
                assignment,
                TeachingAssignment,
            ):
                raise TypeError(
                    "all assignments must be "
                    "TeachingAssignment instances"
                )

            if (
                assignment.owner_id
                != teacher_id
            ):
                continue

            if (
                assignment.status
                is not TeachingAssignmentStatus.ACTIVE
            ):
                continue

            if (
                assignment.role
                is not TeachingAssignmentRole.TEACHING
            ):
                continue

            if assignment.assignment_id in result:
                raise ValueError(
                    "duplicate active teaching "
                    "assignment: "
                    f"{assignment.assignment_id}"
                )

            result[
                assignment.assignment_id
            ] = assignment

        return result

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
