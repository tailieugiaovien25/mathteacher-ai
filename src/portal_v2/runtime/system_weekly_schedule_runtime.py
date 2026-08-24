from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.adapters.academic_week_payload_adapter import (
    AcademicWeekPayloadAdapter,
)
from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from educational_planning_v2.adapters.supabase_operational_data_source_repository import (
    SupabaseOperationalDataSourceRepository,
)
from educational_planning_v2.adapters.supabase_operational_payload_repository import (
    SupabaseOperationalPayloadRepository,
)
from educational_planning_v2.adapters.supabase_teacher_timetable_repository import (
    SupabaseTeacherTimetableRepository,
)
from educational_planning_v2.adapters.supabase_teaching_assignment_repository import (
    SupabaseTeachingAssignmentRepository,
)
from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
    SupabaseAcademicYearConfigurationRepository,
)
from educational_planning_v2.adapters.supabase_academic_week_repository import (
    SupabaseAcademicWeekRepository,
)
from educational_planning_v2.adapters.supabase_class_catalog_repository import (
    SupabaseClassCatalogRepository,
)
from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.models.academic_week_configuration import (
    AcademicWeekStatus,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlotStatus,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadReference,
)
from educational_planning_v2.models.weekly_teaching_schedule import (
    AcademicWeek,
    WeeklyTeachingSchedule,
)
from educational_planning_v2.services.ppct_scope_catalog import (
    PPCTScopeCatalog,
    PPCTScopeOption,
)
from educational_planning_v2.services.auto_ppct_scope_mapping_service import (
    AutoPPCTScopeMappingService,
)
from educational_planning_v2.services.ppct_scope_resolver import (
    PPCTScopeMappingRule,
    PPCTScopeResolver,
)
from educational_planning_v2.services.weekly_schedule_application_service import (
    WeeklyScheduleApplicationRequest,
    WeeklyScheduleApplicationService,
)


@dataclass(frozen=True)
class SystemWeeklyScheduleRuntimeRequest:
    schedule_id: str
    academic_year: str
    week_number: int
    ppct_scope_rules: tuple[
        PPCTScopeMappingRule,
        ...,
    ]


class SystemWeeklyScheduleRuntime:
    """
    Portal/runtime boundary for generating a weekly schedule
    from authenticated system data.

    This runtime wires concrete Supabase adapters to the existing
    application service. It owns no educational business rules.
    """

    def __init__(
        self,
        *,
        client,
        user_id: str,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        if not isinstance(
            user_id,
            str,
        ):
            raise TypeError(
                "user_id must be str"
            )

        normalized_user_id = (
            user_id.strip()
        )

        if not normalized_user_id:
            raise ValueError(
                "user_id must not be empty"
            )

        self._client = client
        self._user_id = normalized_user_id

        self._assignment_repository = (
            SupabaseTeachingAssignmentRepository(
                client=client,
                user_id=self._user_id,
            )
        )

        self._academic_year_repository = (
            SupabaseAcademicYearConfigurationRepository(
                client=client,
            )
        )

        self._academic_week_repository = (
            SupabaseAcademicWeekRepository(
                client=client,
            )
        )

        self._class_repository = (
            SupabaseClassCatalogRepository(
                client=client,
            )
        )

        self._subject_repository = (
            SupabaseSubjectCatalogRepository(
                client=client,
            )
        )

        self._auto_ppct_mapping_service = (
            AutoPPCTScopeMappingService()
        )

        self._timetable_repository = (
            SupabaseTeacherTimetableRepository(
                client=client,
                user_id=self._user_id,
            )
        )

        self._source_repository = (
            SupabaseOperationalDataSourceRepository(
                client=client,
                user_id=self._user_id,
            )
        )

        self._payload_repository = (
            SupabaseOperationalPayloadRepository(
                client=client,
                user_id=self._user_id,
            )
        )

        self._week_adapter = (
            AcademicWeekPayloadAdapter()
        )

        self._ppct_scope_catalog = (
            PPCTScopeCatalog()
        )

    def list_ppct_scope_options(
        self,
        *,
        academic_year: str,
    ) -> tuple[PPCTScopeOption, ...]:
        rows = self._load_active_ppct_rows(
            academic_year=academic_year,
        )

        return (
            self._ppct_scope_catalog.build_options(
                rows=rows,
            )
        )

    def _load_active_ppct_rows(
        self,
        *,
        academic_year: str,
    ) -> tuple[PPCTRow, ...]:
        if not isinstance(
            academic_year,
            str,
        ):
            raise TypeError(
                "academic_year must be str"
            )

        normalized_year = (
            academic_year.strip()
        )

        if not normalized_year:
            raise ValueError(
                "academic_year must not be empty"
            )

        sources = (
            self._source_repository.list_sources(
                owner_id=self._user_id,
                academic_year=normalized_year,
                data_type=OperationalDataType.PPCT,
                status=OperationalDataStatus.ACTIVE,
            )
        )

        if len(sources) != 1:
            raise ValueError(
                "exactly one ACTIVE PPCT "
                "source is required"
            )

        source = sources[0]

        envelope = (
            self._payload_repository.get(
                reference=OperationalPayloadReference(
                    source_id=source.source_id,
                    data_type=OperationalDataType.PPCT,
                    payload_version=(
                        source.source_version
                    ),
                )
            )
        )

        if envelope is None:
            raise LookupError(
                "ACTIVE PPCT payload not found"
            )

        payload = envelope.payload

        if not isinstance(
            payload,
            (tuple, list),
        ):
            raise TypeError(
                "PPCT payload must be a sequence"
            )

        rows = []

        for item in payload:
            if not isinstance(
                item,
                dict,
            ):
                raise TypeError(
                    "PPCT payload row must be dict"
                )

            rows.append(
                PPCTRow(
                    subject_grade=item[
                        "subject_grade"
                    ],
                    period=int(
                        item["period"]
                    ),
                    lesson_name=item[
                        "lesson_name"
                    ],
                    sub_subject=item.get(
                        "sub_subject"
                    ),
                )
            )

        return tuple(rows)

    def _build_auto_ppct_scope_rules(
        self,
        *,
        academic_year: str,
    ) -> tuple[PPCTScopeMappingRule, ...]:
        assignments = (
            self._assignment_repository
            .list_assignments(
                owner_id=self._user_id,
                academic_year=academic_year,
                role=TeachingAssignmentRole.TEACHING,
                status=TeachingAssignmentStatus.ACTIVE,
            )
        )

        timetable_slots = (
            self._timetable_repository.list_slots(
                owner_id=self._user_id,
                academic_year=academic_year,
                status=TeacherTimetableSlotStatus.ACTIVE,
            )
        )
        scheduled_assignment_ids = {
            slot.assignment_id
            for slot in timetable_slots
        }
        assignments = tuple(
            assignment
            for assignment in assignments
            if assignment.assignment_id
            in scheduled_assignment_ids
        )

        if not assignments:
            raise LookupError(
                "no ACTIVE teaching assignments found"
            )

        options = self.list_ppct_scope_options(
            academic_year=academic_year,
        )

        if not options:
            raise LookupError(
                "no PPCT scope options found"
            )

        rules = []

        for assignment in assignments:
            class_item = (
                self._class_repository.get(
                    class_id=assignment.class_id,
                )
            )

            if class_item is None:
                raise LookupError(
                    "class catalog item not found: "
                    f"{assignment.class_id}"
                )

            subject = (
                self._subject_repository
                .get_subject(
                    subject_id=(
                        assignment.subject_ref
                    ),
                )
            )

            if subject is None:
                raise LookupError(
                    "subject catalog item not found: "
                    f"{assignment.subject_ref}"
                )

            component = None

            if assignment.component_ref is not None:
                component = (
                    self._subject_repository
                    .get_component(
                        component_id=(
                            assignment.component_ref
                        ),
                    )
                )

                if component is None:
                    raise LookupError(
                        "subject component not found: "
                        f"{assignment.component_ref}"
                    )

            result = (
                self._auto_ppct_mapping_service
                .resolve(
                    assignment=assignment,
                    class_item=class_item,
                    subject=subject,
                    component=component,
                    options=options,
                )
            )

            rules.append(
                result.rule
            )

        return tuple(rules)

    def generate(
        self,
        *,
        request: SystemWeeklyScheduleRuntimeRequest,
    ) -> WeeklyTeachingSchedule:
        if not isinstance(
            request,
            SystemWeeklyScheduleRuntimeRequest,
        ):
            raise TypeError(
                "request must be "
                "SystemWeeklyScheduleRuntimeRequest"
            )

        academic_week = (
            self._resolve_academic_week(
                academic_year=(
                    request.academic_year
                ),
                week_number=(
                    request.week_number
                ),
            )
        )

        ppct_scope_rules = (
            request.ppct_scope_rules
        )

        if not ppct_scope_rules:
            ppct_scope_rules = (
                self._build_auto_ppct_scope_rules(
                    academic_year=(
                        request.academic_year
                    ),
                )
            )

        scope_resolver = PPCTScopeResolver(
            rules=ppct_scope_rules,
        )

        service = (
            WeeklyScheduleApplicationService(
                assignment_repository=(
                    self._assignment_repository
                ),
                timetable_repository=(
                    self._timetable_repository
                ),
                source_repository=(
                    self._source_repository
                ),
                payload_repository=(
                    self._payload_repository
                ),
                ppct_scope_resolver=(
                    scope_resolver.resolve
                ),
            )
        )

        return service.generate(
            request=WeeklyScheduleApplicationRequest(
                schedule_id=request.schedule_id,
                owner_id=self._user_id,
                academic_year=(
                    request.academic_year
                ),
                academic_week=academic_week,
            )
        )

    def _resolve_academic_week(
        self,
        *,
        academic_year: str,
        week_number: int,
    ) -> AcademicWeek:
        current_year = (
            self._academic_year_repository
            .get_current()
        )

        if current_year is None:
            raise LookupError(
                "current academic year "
                "configuration not found"
            )

        if (
            current_year.academic_year
            != academic_year
        ):
            raise ValueError(
                "requested academic year does not "
                "match current ADMIN academic year"
            )

        configured_week = (
            self._academic_week_repository
            .get_week(
                academic_year_id=(
                    current_year.academic_year_id
                ),
                week_number=week_number,
            )
        )

        if configured_week is None:
            raise LookupError(
                "ADMIN academic week not found "
                f"for week {week_number}"
            )

        if (
            configured_week.status
            != AcademicWeekStatus.ACTIVE
        ):
            raise ValueError(
                "ADMIN academic week is not ACTIVE"
            )

        if (
            configured_week.academic_year
            != academic_year
        ):
            raise ValueError(
                "ADMIN academic week belongs to "
                "another academic year"
            )

        return AcademicWeek(
            academic_year=(
                configured_week.academic_year
            ),
            week_number=(
                configured_week.week_number
            ),
            start_date=(
                configured_week.start_date
            ),
            end_date=(
                configured_week.end_date
            ),
        )

