from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    Subject,
    SubjectComponentPolicy,
)
from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignment,
    TeacherSubjectAssignmentStatus,
)
from lesson_planning_v2.services.teacher_lesson_plan_subject_service import (
    TeacherLessonPlanSubjectService,
)


class FakeAssignmentRepository:
    def __init__(self, assignments):
        self.assignments = tuple(assignments)
        self.calls = []

    def list_assignments(
        self,
        *,
        teacher_id=None,
        academic_year=None,
        status=None,
    ):
        self.calls.append(
            {
                "teacher_id": teacher_id,
                "academic_year": academic_year,
                "status": status,
            }
        )

        return tuple(
            item
            for item in self.assignments
            if (
                (teacher_id is None or item.teacher_id == teacher_id)
                and (
                    academic_year is None
                    or item.academic_year == academic_year
                )
                and (
                    status is None
                    or item.status is status
                )
            )
        )


class FakeSubjectRepository:
    def __init__(self, subjects):
        self.subjects = {
            item.subject_id: item
            for item in subjects
        }
        self.requested_ids = []

    def get_subject(
        self,
        *,
        subject_id,
    ):
        self.requested_ids.append(subject_id)
        return self.subjects.get(subject_id)


def assignment(
    assignment_id,
    subject_id,
    *,
    teacher_id="teacher-1",
    academic_year="2026-2027",
    status=TeacherSubjectAssignmentStatus.ACTIVE,
):
    return TeacherSubjectAssignment(
        assignment_id=assignment_id,
        teacher_id=teacher_id,
        academic_year=academic_year,
        subject_id=subject_id,
        status=status,
    )


def subject(
    subject_id,
    code,
    name,
    *,
    display_order=0,
    status=CatalogStatus.ACTIVE,
):
    return Subject(
        subject_id=subject_id,
        code=code,
        name=name,
        component_policy=SubjectComponentPolicy.NONE,
        status=status,
        display_order=display_order,
    )


def build_service(
    assignments,
    subjects,
):
    assignment_repository = (
        FakeAssignmentRepository(assignments)
    )
    subject_repository = (
        FakeSubjectRepository(subjects)
    )

    service = TeacherLessonPlanSubjectService(
        assignment_repository=assignment_repository,
        subject_repository=subject_repository,
    )

    return (
        service,
        assignment_repository,
        subject_repository,
    )


def test_lists_multiple_subjects_for_teacher():
    service, _, _ = build_service(
        assignments=(
            assignment("a1", "subject-math"),
            assignment("a2", "subject-it"),
        ),
        subjects=(
            subject(
                "subject-math",
                "MATH",
                "Toan",
                display_order=10,
            ),
            subject(
                "subject-it",
                "IT",
                "Tin hoc",
                display_order=20,
            ),
        ),
    )

    result = service.list_subjects(
        teacher_id="teacher-1",
        academic_year="2026-2027",
    )

    assert tuple(
        item.subject_id
        for item in result
    ) == (
        "subject-math",
        "subject-it",
    )


def test_uses_active_teacher_assignment_filter():
    service, repository, _ = build_service(
        assignments=(),
        subjects=(),
    )

    service.list_subjects(
        teacher_id="teacher-1",
        academic_year="2026-2027",
    )

    assert repository.calls == [
        {
            "teacher_id": "teacher-1",
            "academic_year": "2026-2027",
            "status": (
                TeacherSubjectAssignmentStatus.ACTIVE
            ),
        }
    ]


def test_deduplicates_subject_id():
    service, _, repository = build_service(
        assignments=(
            assignment("a1", "subject-math"),
            assignment("a2", "subject-math"),
        ),
        subjects=(
            subject(
                "subject-math",
                "MATH",
                "Toan",
            ),
        ),
    )

    result = service.list_subjects(
        teacher_id="teacher-1",
        academic_year="2026-2027",
    )

    assert len(result) == 1
    assert repository.requested_ids == [
        "subject-math"
    ]


def test_skips_missing_catalog_subject():
    service, _, _ = build_service(
        assignments=(
            assignment("a1", "missing"),
        ),
        subjects=(),
    )

    result = service.list_subjects(
        teacher_id="teacher-1",
        academic_year="2026-2027",
    )

    assert result == ()


def test_skips_inactive_catalog_subject():
    service, _, _ = build_service(
        assignments=(
            assignment("a1", "subject-old"),
        ),
        subjects=(
            subject(
                "subject-old",
                "OLD",
                "Old subject",
                status=CatalogStatus.INACTIVE,
            ),
        ),
    )

    result = service.list_subjects(
        teacher_id="teacher-1",
        academic_year="2026-2027",
    )

    assert result == ()


def test_orders_by_display_order_then_name():
    service, _, _ = build_service(
        assignments=(
            assignment("a1", "subject-b"),
            assignment("a2", "subject-c"),
            assignment("a3", "subject-a"),
        ),
        subjects=(
            subject(
                "subject-b",
                "B",
                "Beta",
                display_order=20,
            ),
            subject(
                "subject-c",
                "C",
                "Charlie",
                display_order=10,
            ),
            subject(
                "subject-a",
                "A",
                "Alpha",
                display_order=10,
            ),
        ),
    )

    result = service.list_subjects(
        teacher_id="teacher-1",
        academic_year="2026-2027",
    )

    assert tuple(
        item.subject_id
        for item in result
    ) == (
        "subject-a",
        "subject-c",
        "subject-b",
    )


def test_rejects_blank_teacher_id():
    service, _, _ = build_service(
        assignments=(),
        subjects=(),
    )

    try:
        service.list_subjects(
            teacher_id="   ",
            academic_year="2026-2027",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_rejects_blank_academic_year():
    service, _, _ = build_service(
        assignments=(),
        subjects=(),
    )

    try:
        service.list_subjects(
            teacher_id="teacher-1",
            academic_year=" ",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError"
        )
