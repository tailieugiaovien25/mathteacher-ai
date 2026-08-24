from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from educational_planning_v2.models.weekly_teaching_schedule import (
    AcademicWeek,
    CurriculumPeriod,
    LessonExecutionRecord,
    TimetableSlot,
    WeeklyTeachingSchedule,
    WeeklyTeachingScheduleEntry,
)


class WeeklyTeachingScheduleService:
    """Build a teacher's weekly schedule from canonical domain data.

    The service intentionally knows nothing about physical storage,
    source-file layout, table names, or user-interface controls.
    """

    def build(
        self,
        *,
        schedule_id: str,
        teacher_id: str,
        academic_week: AcademicWeek,
        timetable_slots: tuple[TimetableSlot, ...],
        curriculum_periods: tuple[CurriculumPeriod, ...],
        execution_records: tuple[LessonExecutionRecord, ...] = (),
    ) -> WeeklyTeachingSchedule:
        self._require_tuple(timetable_slots, "timetable_slots")
        self._require_tuple(curriculum_periods, "curriculum_periods")
        self._require_tuple(execution_records, "execution_records")

        if not isinstance(academic_week, AcademicWeek):
            raise TypeError("academic_week must be an AcademicWeek")

        normalized_teacher_id = self._required_text(
            teacher_id,
            "teacher_id",
        )

        relevant_slots = tuple(
            slot
            for slot in timetable_slots
            if self._is_relevant_slot(
                slot=slot,
                teacher_id=normalized_teacher_id,
                academic_week=academic_week,
            )
        )

        curriculum_index = self._build_curriculum_index(curriculum_periods)
        completed_counts = self._completed_counts(
            execution_records=execution_records,
            teacher_id=normalized_teacher_id,
            before_date=academic_week.start_date,
        )

        baseline_source = "EXECUTION_RECORDS"

        if not execution_records:
            completed_counts = (
                self._scheduled_counts_before_week(
                    timetable_slots=timetable_slots,
                    teacher_id=normalized_teacher_id,
                    academic_week=academic_week,
                )
            )
            baseline_source = "TIMETABLE_FALLBACK"
        occurrences: Counter[tuple[str, str, str | None]] = Counter()
        entries: list[WeeklyTeachingScheduleEntry] = []

        dated_slot_index = {}

        for slot in relevant_slots:
            teaching_date = (
                academic_week.start_date
                + timedelta(days=slot.weekday - 1)
            )
            occurrence_key = self._slot_occurrence_key(
                teaching_date=teaching_date,
                slot=slot,
            )
            dated_slot_index.setdefault(
                occurrence_key,
                (teaching_date, slot),
            )

        duplicate_slot_count = (
            len(relevant_slots)
            - len(dated_slot_index)
        )

        dated_slots = sorted(
            dated_slot_index.values(),
            key=lambda item: (
                item[0],
                (
                    0
                    if item[1].session.value
                    == "MORNING"
                    else 1
                ),
                item[1].timetable_period,
                item[1].class_id,
                item[1].subject_ref,
                item[1].component_ref or "",
            ),
        )

        for teaching_date, slot in dated_slots:
            if teaching_date > academic_week.end_date:
                continue

            key = slot.curriculum_key
            occurrences[key] += 1
            period_number = completed_counts[key] + occurrences[key]
            curriculum = curriculum_index.get((key, period_number))

            if curriculum is None:
                raise ValueError(
                    "missing curriculum period for "
                    f"class={slot.class_id!r}, "
                    f"subject={slot.subject_ref!r}, "
                    f"component={slot.component_ref!r}, "
                    f"period={period_number}"
                )

            entries.append(
                WeeklyTeachingScheduleEntry(
                    teaching_date=teaching_date,
                    weekday=slot.weekday,
                    timetable_period=slot.timetable_period,
                    session=slot.session,
                    teacher_id=normalized_teacher_id,
                    class_id=slot.class_id,
                    subject_ref=slot.subject_ref,
                    component_ref=slot.component_ref,
                    curriculum_period=curriculum.period_number,
                    lesson_id=curriculum.lesson_id,
                    lesson_title=curriculum.lesson_title,
                    period_in_lesson=curriculum.period_in_lesson,
                    total_lesson_periods=curriculum.total_lesson_periods,
                    teaching_equipment=curriculum.teaching_equipment,
                )
            )

        return WeeklyTeachingSchedule(
            schedule_id=schedule_id,
            teacher_id=normalized_teacher_id,
            academic_week=academic_week,
            entries=tuple(entries),
            metadata={
                "timetable_slot_count": len(dated_slots),
                "duplicate_timetable_slot_count": (
                    duplicate_slot_count
                ),
                "completed_execution_count": sum(completed_counts.values()),
                "period_baseline_source": baseline_source,
            },
        )

    @classmethod
    def _scheduled_counts_before_week(
        cls,
        *,
        timetable_slots: tuple[TimetableSlot, ...],
        teacher_id: str,
        academic_week: AcademicWeek,
    ) -> Counter[tuple[str, str, str | None]]:
        """Estimate prior periods from dated TKB occurrences.

        This is used only while no persisted execution history exists.
        Exact duplicate occurrences are counted once; morning and
        afternoon occurrences remain distinct.
        """

        result: Counter[
            tuple[str, str, str | None]
        ] = Counter()
        seen_occurrences = set()
        last_date = (
            academic_week.start_date
            - timedelta(days=1)
        )

        for slot in timetable_slots:
            if slot.teacher_id != teacher_id:
                continue

            occurrence_date = cls._first_weekday_on_or_after(
                start_date=slot.effective_from,
                weekday=slot.weekday,
            )
            occurrence_end = min(
                slot.effective_to,
                last_date,
            )

            while occurrence_date <= occurrence_end:
                occurrence_key = cls._slot_occurrence_key(
                    teaching_date=occurrence_date,
                    slot=slot,
                )

                if occurrence_key not in seen_occurrences:
                    seen_occurrences.add(occurrence_key)
                    result[slot.curriculum_key] += 1

                occurrence_date += timedelta(days=7)

        return result

    @staticmethod
    def _first_weekday_on_or_after(
        *,
        start_date: date,
        weekday: int,
    ) -> date:
        target_python_weekday = weekday - 1
        offset = (
            target_python_weekday
            - start_date.weekday()
        ) % 7
        return start_date + timedelta(days=offset)

    @staticmethod
    def _slot_occurrence_key(
        *,
        teaching_date: date,
        slot: TimetableSlot,
    ) -> tuple:
        return (
            teaching_date,
            slot.session.value,
            slot.timetable_period,
            slot.teacher_id,
            slot.class_id,
            slot.subject_ref,
            slot.component_ref or "",
        )

    @staticmethod
    def _is_relevant_slot(
        *,
        slot: TimetableSlot,
        teacher_id: str,
        academic_week: AcademicWeek,
    ) -> bool:
        if not isinstance(slot, TimetableSlot):
            raise TypeError("all timetable_slots must be TimetableSlot instances")

        teaching_date = academic_week.start_date + timedelta(
            days=slot.weekday - 1
        )

        return (
            slot.teacher_id == teacher_id
            and teaching_date <= academic_week.end_date
            and slot.effective_from <= teaching_date <= slot.effective_to
        )

    @staticmethod
    def _build_curriculum_index(
        curriculum_periods: tuple[CurriculumPeriod, ...],
    ) -> dict[
        tuple[tuple[str, str, str | None], int],
        CurriculumPeriod,
    ]:
        result = {}

        for curriculum in curriculum_periods:
            if not isinstance(curriculum, CurriculumPeriod):
                raise TypeError(
                    "all curriculum_periods must be CurriculumPeriod instances"
                )

            index_key = (curriculum.curriculum_key, curriculum.period_number)

            if index_key in result:
                raise ValueError(
                    "duplicate curriculum period: "
                    f"key={curriculum.curriculum_key!r}, "
                    f"period={curriculum.period_number}"
                )

            result[index_key] = curriculum

        return result

    @staticmethod
    def _completed_counts(
        *,
        execution_records: tuple[LessonExecutionRecord, ...],
        teacher_id: str,
        before_date,
    ) -> Counter[tuple[str, str, str | None]]:
        result: Counter[tuple[str, str, str | None]] = Counter()

        for record in execution_records:
            if not isinstance(record, LessonExecutionRecord):
                raise TypeError(
                    "all execution_records must be LessonExecutionRecord instances"
                )

            if (
                record.teacher_id == teacher_id
                and record.teaching_date < before_date
                and record.is_completed
            ):
                result[record.curriculum_key] += 1

        return result

    @staticmethod
    def _require_tuple(value, field_name: str) -> None:
        if not isinstance(value, tuple):
            raise TypeError(f"{field_name} must be a tuple")

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} must not be empty")

        return normalized
