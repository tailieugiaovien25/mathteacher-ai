from datetime import date

from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.services.teacher_timetable_assignment_bridge import (
    TeacherTimetableAssignmentBridge,
)
from educational_planning_v2.services.teacher_timetable_subject_scope_service import (
    TeacherTimetableSubjectScope,
)


def assignment(
    *,
    assignment_id="assignment-001",
    class_id="6A1",
    subject_ref="Toan",
    component_ref=None,
):
    return TeachingAssignment(
        assignment_id=assignment_id,
        owner_id="teacher-001",
        academic_year="2026-2027",
        class_id=class_id,
        role=TeachingAssignmentRole.TEACHING,
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
        subject_ref=subject_ref,
        component_ref=component_ref,
    )


def scope(
    *,
    subject_id="subject-math",
    subject_name="Toan",
    component_id=None,
    component_name=None,
):
    return TeacherTimetableSubjectScope(
        subject_id=subject_id,
        subject_name=subject_name,
        component_id=component_id,
        component_name=component_name,
    )


def test_subject_level_registration_matches_assignment():
    options = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(
                assignment(),
            ),
            subject_scopes=(
                scope(),
            ),
        )
    )

    assert len(options) == 1

    option = options[0]

    assert option.class_id == "6A1"
    assert option.subject_id == "subject-math"
    assert option.component_id is None
    assert (
        option.assignment_id
        == "assignment-001"
    )


def test_component_registration_matches_assignment():
    options = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(
                assignment(
                    component_ref="Dai so",
                ),
            ),
            subject_scopes=(
                scope(
                    component_id=(
                        "component-math-algebra"
                    ),
                    component_name="Dai so",
                ),
            ),
        )
    )

    assert len(options) == 1

    assert (
        options[0].component_id
        == "component-math-algebra"
    )


def test_parent_subject_assignment_does_not_restrict_registered_component():
    options = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(
                assignment(
                    subject_ref="Toan",
                    component_ref="Hinh hoc",
                ),
            ),
            subject_scopes=(
                scope(
                    component_id=(
                        "component-math-algebra"
                    ),
                    component_name="Dai so",
                ),
            ),
        )
    )

    assert len(options) == 1

    assert (
        options[0].component_id
        == "component-math-algebra"
    )


def test_component_level_legacy_assignment_keeps_component_restriction():
    options = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(
                assignment(
                    subject_ref="Hinh hoc",
                    component_ref=None,
                ),
            ),
            subject_scopes=(
                scope(
                    component_id=(
                        "component-math-algebra"
                    ),
                    component_name="Dai so",
                ),
            ),
        )
    )

    assert options == ()


def test_legacy_component_in_subject_ref_matches():
    options = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(
                assignment(
                    subject_ref="Hinh hoc",
                    component_ref=None,
                ),
            ),
            subject_scopes=(
                scope(
                    component_id=(
                        "component-math-geometry"
                    ),
                    component_name="Hinh hoc",
                ),
            ),
        )
    )

    assert len(options) == 1

    assert (
        options[0].component_id
        == "component-math-geometry"
    )


def test_xstk_legacy_alias_matches_sxtk():
    options = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(
                assignment(
                    component_ref="XSTK",
                ),
            ),
            subject_scopes=(
                scope(
                    component_id=(
                        "component-math-statistics-probability"
                    ),
                    component_name="SXTK",
                ),
            ),
        )
    )

    assert len(options) == 1


def test_component_of_other_subject_does_not_match():
    options = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(
                assignment(
                    subject_ref="Toan",
                    component_ref="Dai so",
                ),
            ),
            subject_scopes=(
                scope(
                    subject_id="subject-art",
                    subject_name="Nghe thuat",
                    component_id=(
                        "component-art-music"
                    ),
                    component_name="Am nhac",
                ),
            ),
        )
    )

    assert options == ()


def test_same_scope_in_different_classes_is_preserved():
    options = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(
                assignment(
                    assignment_id="a1",
                    class_id="6A1",
                ),
                assignment(
                    assignment_id="a2",
                    class_id="6A2",
                ),
            ),
            subject_scopes=(
                scope(),
            ),
        )
    )

    assert len(options) == 2

    assert {
        item.class_id
        for item in options
    } == {
        "6A1",
        "6A2",
    }


def test_canonical_subject_id_assignment_covers_subject_components():
    assignment = TeachingAssignment(
        assignment_id="assign-math",
        owner_id="teacher-1",
        academic_year="2026-2027",
        class_id="7A2",
        subject_ref="subject-math",
        component_ref=None,
        role=TeachingAssignmentRole.TEACHING,
        effective_from=date(2026, 8, 24),
        effective_to=date(2027, 5, 31),
        status=TeachingAssignmentStatus.ACTIVE,
    )

    scopes = (
        TeacherTimetableSubjectScope(
            subject_id="subject-math",
            subject_name="To?n",
            component_id="component-algebra",
            component_name="??i s?",
        ),
        TeacherTimetableSubjectScope(
            subject_id="subject-math",
            subject_name="To?n",
            component_id="component-geometry",
            component_name="H?nh h?c",
        ),
    )

    result = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(assignment,),
            subject_scopes=scopes,
        )
    )

    assert {
        item.component_id
        for item in result
    } == {
        "component-algebra",
        "component-geometry",
    }


def test_canonical_component_id_assignment_only_matches_component():
    assignment = TeachingAssignment(
        assignment_id="assign-geometry",
        owner_id="teacher-1",
        academic_year="2026-2027",
        class_id="6A1",
        subject_ref="subject-math",
        component_ref="component-geometry",
        role=TeachingAssignmentRole.TEACHING,
        effective_from=date(2026, 8, 24),
        effective_to=date(2027, 5, 31),
        status=TeachingAssignmentStatus.ACTIVE,
    )

    scopes = (
        TeacherTimetableSubjectScope(
            subject_id="subject-math",
            subject_name="To?n",
            component_id="component-algebra",
            component_name="??i s?",
        ),
        TeacherTimetableSubjectScope(
            subject_id="subject-math",
            subject_name="To?n",
            component_id="component-geometry",
            component_name="H?nh h?c",
        ),
    )

    result = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=(assignment,),
            subject_scopes=scopes,
        )
    )

    assert len(result) == 1
    assert (
        result[0].component_id
        == "component-geometry"
    )
