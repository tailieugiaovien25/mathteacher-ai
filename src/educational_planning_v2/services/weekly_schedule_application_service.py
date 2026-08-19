from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from educational_planning_v2.builders.weekly_schedule_input_builder import (
    WeeklyScheduleInputBuilder,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadReference,
)
from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlotStatus,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.models.weekly_teaching_schedule import (
    AcademicWeek,
    WeeklyTeachingSchedule,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)
from educational_planning_v2.repositories.operational_payload_repository import (
    OperationalPayloadRepository,
)
from educational_planning_v2.repositories.teacher_timetable_repository import (
    TeacherTimetableRepository,
)
from educational_planning_v2.repositories.teaching_assignment_repository import (
    TeachingAssignmentRepository,
)
from educational_planning_v2.services.weekly_teaching_schedule_service import (
    WeeklyTeachingScheduleService,
)


PPCTScopeResolver = Callable[
    [
        TeachingAssignment,
        tuple[PPCTRow, ...],
    ],
    tuple[PPCTRow, ...],
]


@dataclass(frozen=True)
class WeeklyScheduleApplicationRequest:
    schedule_id: str
    owner_id: str
    academic_year: str
    academic_week: AcademicWeek


class WeeklyScheduleApplicationService:
    """
    Assemble canonical weekly-schedule inputs from repository data.

    This application service coordinates repository ports only.
    It owns no Supabase, SQL, workbook, Streamlit, or textbook rules.
    """

    def __init__(
        self,
        *,
        assignment_repository: TeachingAssignmentRepository,
        timetable_repository: TeacherTimetableRepository,
        source_repository: OperationalDataSourceRepository,
        payload_repository: OperationalPayloadRepository,
        ppct_scope_resolver: PPCTScopeResolver,
        input_builder: WeeklyScheduleInputBuilder | None = None,
        schedule_service: WeeklyTeachingScheduleService | None = None,
    ) -> None:
        if not callable(ppct_scope_resolver):
            raise TypeError(
                "ppct_scope_resolver must be callable"
            )

        self._assignment_repository = (
            assignment_repository
        )
        self._timetable_repository = (
            timetable_repository
        )
        self._source_repository = (
            source_repository
        )
        self._payload_repository = (
            payload_repository
        )
        self._ppct_scope_resolver = (
            ppct_scope_resolver
        )
        self._input_builder = (
            input_builder
            or WeeklyScheduleInputBuilder()
        )
        self._schedule_service = (
            schedule_service
            or WeeklyTeachingScheduleService()
        )

    def generate(
        self,
        *,
        request: WeeklyScheduleApplicationRequest,
    ) -> WeeklyTeachingSchedule:
        if not isinstance(
            request,
            WeeklyScheduleApplicationRequest,
        ):
            raise TypeError(
                "request must be "
                "WeeklyScheduleApplicationRequest"
            )

        if (
            request.academic_week.academic_year
            != request.academic_year
        ):
            raise ValueError(
                "academic week year does not match request"
            )

        assignments = (
            self._assignment_repository.list_assignments(
                owner_id=request.owner_id,
                academic_year=request.academic_year,
                role=TeachingAssignmentRole.TEACHING,
                status=TeachingAssignmentStatus.ACTIVE,
            )
        )

        timetable_slots = (
            self._timetable_repository.list_slots(
                owner_id=request.owner_id,
                academic_year=request.academic_year,
                status=(
                    TeacherTimetableSlotStatus.ACTIVE
                ),
            )
        )

        canonical_timetable = (
            self._input_builder.build_timetable_slots(
                teacher_id=request.owner_id,
                timetable_slots=timetable_slots,
                assignments=assignments,
            )
        )

        ppct_rows = self._load_active_ppct_rows(
            owner_id=request.owner_id,
            academic_year=request.academic_year,
        )

        curriculum_periods = []

        for assignment in assignments:
            scoped_rows = (
                self._ppct_scope_resolver(
                    assignment,
                    ppct_rows,
                )
            )

            if not isinstance(
                scoped_rows,
                tuple,
            ):
                raise TypeError(
                    "ppct_scope_resolver must return tuple"
                )

            if not scoped_rows:
                continue

            curriculum_periods.extend(
                self._input_builder
                .build_curriculum_periods(
                    assignment=assignment,
                    ppct_rows=scoped_rows,
                )
            )

        return self._schedule_service.build(
            schedule_id=request.schedule_id,
            teacher_id=request.owner_id,
            academic_week=request.academic_week,
            timetable_slots=canonical_timetable,
            curriculum_periods=tuple(
                curriculum_periods
            ),
            execution_records=(),
        )

    def _load_active_ppct_rows(
        self,
        *,
        owner_id: str,
        academic_year: str,
    ) -> tuple[PPCTRow, ...]:
        sources = (
            self._source_repository.list_sources(
                owner_id=owner_id,
                academic_year=academic_year,
                data_type=OperationalDataType.PPCT,
                status=OperationalDataStatus.ACTIVE,
            )
        )

        if len(sources) != 1:
            raise ValueError(
                "exactly one ACTIVE PPCT source is required"
            )

        source = sources[0]

        envelope = self._payload_repository.get(
            reference=OperationalPayloadReference(
                source_id=source.source_id,
                data_type=OperationalDataType.PPCT,
                payload_version=(
                    source.source_version
                ),
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
