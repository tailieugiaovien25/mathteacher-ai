from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from educational_planning_v2.adapters.supabase_class_catalog_repository import SupabaseClassCatalogRepository
from educational_planning_v2.adapters.supabase_weekly_schedule_repository import SupabaseWeeklyScheduleRepository
from lesson_planning_v2.adapters.supabase_lesson_plan_grouping_policy_repository import SupabaseLessonPlanGroupingPolicyRepository
from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode, LessonPlanGroupingPolicy
from lesson_planning_v2.services.lesson_plan_grouping_service import LessonPlanGroupingPolicyResolver, LessonPlanGroupingService


class WeeklyLessonPlanGroupProviderError(RuntimeError):
    pass


class _FailClosedPolicyResolver(LessonPlanGroupingPolicyResolver):
    def __init__(self, policies):
        super().__init__(policies)
        self._exact = {(str(p.subject_ref or "").strip(), str(p.component_ref or "").strip()): p.mode for p in policies}
        self._defaults = {str(p.subject_ref or "").strip(): p.mode for p in policies if not str(p.component_ref or "").strip()}

    def resolve(self, *, subject_ref: str, component_ref: str):
        subject = str(subject_ref or "").strip()
        component = str(component_ref or "").strip()
        mode = self._exact.get((subject, component))
        if mode is None:
            mode = self._defaults.get(subject)
        if mode is None:
            raise WeeklyLessonPlanGroupProviderError(
                f"AUTHORITATIVE_GROUPING_POLICY_REQUIRED: {subject}/{component}"
            )
        return mode


class WeeklyLessonPlanGroupProvider:
    def __init__(self, *, client: Any, user_id: str) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self._client = client
        self._user_id = str(user_id or "").strip()
        if not self._user_id:
            raise ValueError("user_id must not be empty")

    def provide(self, *, academic_year: str, week_number: int):
        year = str(academic_year or "").strip()
        week = int(week_number)
        if not year or week <= 0:
            raise ValueError("valid academic_year/week_number required")

        schedule_id = f"SYSTEM-{self._user_id}-{year}-W{week}"
        schedule = SupabaseWeeklyScheduleRepository(self._client, self._user_id).get(schedule_id)
        if schedule is None:
            raise WeeklyLessonPlanGroupProviderError(f"CURRENT_LBG_NOT_FOUND: {schedule_id}")
        if str(schedule.schedule_id) != schedule_id:
            raise WeeklyLessonPlanGroupProviderError("CURRENT_LBG_SCHEDULE_ID_MISMATCH")
        if str(schedule.teacher_id).strip() != self._user_id:
            raise WeeklyLessonPlanGroupProviderError("CURRENT_LBG_TEACHER_MISMATCH")
        if str(schedule.academic_week.academic_year).strip() != year:
            raise WeeklyLessonPlanGroupProviderError("CURRENT_LBG_ACADEMIC_YEAR_MISMATCH")
        if int(schedule.academic_week.week_number) != week:
            raise WeeklyLessonPlanGroupProviderError("CURRENT_LBG_WEEK_MISMATCH")

        entries = tuple(schedule.entries or ())
        if not entries:
            return ()

        try:
            configs = tuple(
                SupabaseLessonPlanGroupingPolicyRepository(client=self._client).list_configs()
            )
        except Exception as exc:
            raise WeeklyLessonPlanGroupProviderError("GROUPING_POLICY_READ_FAILED") from exc

        policies = tuple(
            LessonPlanGroupingPolicy(
                subject_ref=str(c.subject_ref or "").strip(),
                component_ref=str(c.component_ref or "").strip(),
                mode=c.mode,
            )
            for c in configs if bool(getattr(c, "active", False))
        )
        if not policies:
            raise WeeklyLessonPlanGroupProviderError("ACTIVE_GROUPING_POLICY_REQUIRED")

        class_repo = SupabaseClassCatalogRepository(client=self._client)
        cache = {}

        def grade(entry):
            class_id = str(getattr(entry, "class_id", "") or "").strip()
            if not class_id:
                raise WeeklyLessonPlanGroupProviderError("CANONICAL_CLASS_ID_REQUIRED")
            if class_id not in cache:
                try:
                    item = class_repo.get(class_id=class_id)
                except Exception as exc:
                    raise WeeklyLessonPlanGroupProviderError("CLASS_CATALOG_READ_FAILED") from exc
                if item is None:
                    raise WeeklyLessonPlanGroupProviderError(f"CLASS_CATALOG_ENTRY_REQUIRED: {class_id}")
                try:
                    value = int(str(item.grade_level).strip())
                except (TypeError, ValueError) as exc:
                    raise WeeklyLessonPlanGroupProviderError(f"CANONICAL_GRADE_REQUIRED: {class_id}") from exc
                if not 1 <= value <= 12:
                    raise WeeklyLessonPlanGroupProviderError(f"INVALID_CANONICAL_GRADE: {class_id}")
                cache[class_id] = value
            return cache[class_id]

        rows = tuple(
            SimpleNamespace(
                academic_year=year,
                week_number=week,
                subject_ref=str(e.subject_ref or "").strip(),
                component_ref=str(e.component_ref or "").strip(),
                grade=grade(e),
                curriculum_period=e.curriculum_period,
                lesson_id=str(e.lesson_id or "").strip(),
                lesson_title=str(e.lesson_title or "").strip(),
                class_id=str(e.class_id or "").strip(),
                teaching_date=e.teaching_date,
                timetable_period=e.timetable_period,
                timetable_slot_id=None,
                teaching_equipment=tuple(e.teaching_equipment or ()),
            )
            for e in entries
        )
        return LessonPlanGroupingService().group(
            rows,
            policy_resolver=_FailClosedPolicyResolver(policies),
        )
