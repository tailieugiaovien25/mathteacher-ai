from datetime import date

from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
    OperationalPayloadReference,
)
from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlot,
    TeacherTimetableSlotStatus,
    TeachingSession,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.models.weekly_teaching_schedule import (
    AcademicWeek,
)
from educational_planning_v2.services.weekly_schedule_application_service import (
    WeeklyScheduleApplicationRequest,
    WeeklyScheduleApplicationService,
)


class AssignmentRepository:
    def __init__(self, assignments):
        self.assignments = assignments

    def list_assignments(self, **kwargs):
        return self.assignments


class TimetableRepository:
    def __init__(self, slots):
        self.slots = slots

    def list_slots(self, **kwargs):
        return self.slots


class SourceRepository:
    def __init__(self, source):
        self.source = source

    def list_sources(self, **kwargs):
        return (self.source,)


class PayloadRepository:
    def __init__(self, envelope):
        self.envelope = envelope

    def get(self, **kwargs):
        return self.envelope


def test_repository_data_generates_weekly_schedule():
    assignment = TeachingAssignment(
        assignment_id="assignment-1",
        owner_id="teacher-1",
        academic_year="2026-2027",
        class_id="6A1",
        role=TeachingAssignmentRole.TEACHING,
        subject_ref="TOAN",
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
        status=TeachingAssignmentStatus.ACTIVE,
    )

    slot = TeacherTimetableSlot(
        slot_id="slot-1",
        owner_id="teacher-1",
        academic_year="2026-2027",
        assignment_id="assignment-1",
        weekday=1,
        session=TeachingSession.MORNING,
        period=1,
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
        status=TeacherTimetableSlotStatus.ACTIVE,
    )

    source = OperationalDataSource(
        source_id="ppct-1",
        data_type=OperationalDataType.PPCT,
        origin=OperationalDataOrigin.FILE_IMPORTED,
        owner_id="teacher-1",
        academic_year="2026-2027",
        status=OperationalDataStatus.ACTIVE,
        source_version="v1",
    )

    envelope = OperationalPayloadEnvelope(
        reference=OperationalPayloadReference(
            source_id="ppct-1",
            data_type=OperationalDataType.PPCT,
            payload_version="v1",
        ),
        payload=[
            {
                "subject_grade": "To?n 6",
                "period": 1,
                "lesson_name": "B?i m? ??u",
                "sub_subject": None,
            }
        ],
    )

    service = WeeklyScheduleApplicationService(
        assignment_repository=(
            AssignmentRepository(
                (assignment,)
            )
        ),
        timetable_repository=(
            TimetableRepository(
                (slot,)
            )
        ),
        source_repository=(
            SourceRepository(source)
        ),
        payload_repository=(
            PayloadRepository(envelope)
        ),
        ppct_scope_resolver=(
            lambda assignment, rows: rows
        ),
    )

    schedule = service.generate(
        request=WeeklyScheduleApplicationRequest(
            schedule_id="week-1",
            owner_id="teacher-1",
            academic_year="2026-2027",
            academic_week=AcademicWeek(
                academic_year="2026-2027",
                week_number=1,
                start_date=date(
                    2026,
                    9,
                    7,
                ),
                end_date=date(
                    2026,
                    9,
                    13,
                ),
            ),
        )
    )

    assert len(schedule.entries) == 1

    entry = schedule.entries[0]

    assert entry.class_id == "6A1"
    assert entry.subject_ref == "TOAN"
    assert entry.curriculum_period == 1
    assert entry.lesson_title == "B?i m? ??u"
