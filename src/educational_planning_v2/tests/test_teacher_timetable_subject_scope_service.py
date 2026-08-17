from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    Subject,
    SubjectComponent,
    SubjectComponentPolicy,
)
from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)
from educational_planning_v2.services.teacher_timetable_subject_scope_service import (
    TeacherTimetableSubjectScopeService,
)


class FakeCatalogRepository:
    def __init__(
        self,
        *,
        subjects,
        components,
    ):
        self.subjects = {
            item.subject_id: item
            for item in subjects
        }
        self.components = {
            item.component_id: item
            for item in components
        }

    def get_subject(
        self,
        *,
        subject_id,
    ):
        return self.subjects.get(
            subject_id
        )

    def get_component(
        self,
        *,
        component_id,
    ):
        return self.components.get(
            component_id
        )


class FakeRegistrationRepository:
    def __init__(
        self,
        registrations,
    ):
        self.registrations = tuple(
            registrations
        )

    def list_registrations(
        self,
        *,
        owner_id,
        academic_year,
        status=None,
    ):
        return tuple(
            item
            for item in self.registrations
            if (
                item.owner_id == owner_id
                and item.academic_year
                == academic_year
                and (
                    status is None
                    or item.status is status
                )
            )
        )


def build_service(
    registrations,
):
    math = Subject(
        subject_id="subject-math",
        code="MATH",
        name="To\u00e1n",
        component_policy=(
            SubjectComponentPolicy.OPTIONAL
        ),
    )

    geometry = SubjectComponent(
        component_id="component-math-geometry",
        subject_id="subject-math",
        code="GEOMETRY",
        name="H\u00ecnh h\u1ecdc",
    )

    algebra = SubjectComponent(
        component_id="component-math-algebra",
        subject_id="subject-math",
        code="ALGEBRA",
        name="\u0110\u1ea1i s\u1ed1",
    )

    return TeacherTimetableSubjectScopeService(
        catalog_repository=FakeCatalogRepository(
            subjects=(math,),
            components=(
                geometry,
                algebra,
            ),
        ),
        registration_repository=(
            FakeRegistrationRepository(
                registrations
            )
        ),
    )


def test_component_registration_preserves_parent_subject():
    registration = TeacherSubjectRegistration(
        registration_id="registration-001",
        owner_id="teacher-001",
        academic_year="2026-2027",
        subject_id="subject-math",
        component_id="component-math-geometry",
    )

    scopes = build_service(
        (registration,)
    ).list_scopes(
        owner_id="teacher-001",
        academic_year="2026-2027",
    )

    assert len(scopes) == 1

    scope = scopes[0]

    assert scope.subject_id == "subject-math"
    assert scope.subject_name == "To\u00e1n"

    assert (
        scope.component_id
        == "component-math-geometry"
    )

    assert scope.component_name == "H\u00ecnh h\u1ecdc"


def test_subject_level_registration_has_no_component():
    registration = TeacherSubjectRegistration(
        registration_id="registration-001",
        owner_id="teacher-001",
        academic_year="2026-2027",
        subject_id="subject-math",
    )

    scopes = build_service(
        (registration,)
    ).list_scopes(
        owner_id="teacher-001",
        academic_year="2026-2027",
    )

    assert len(scopes) == 1

    assert scopes[0].subject_name == "To\u00e1n"
    assert scopes[0].component_id is None
    assert scopes[0].component_name is None


def test_duplicate_registration_scope_is_collapsed():
    registrations = (
        TeacherSubjectRegistration(
            registration_id="registration-001",
            owner_id="teacher-001",
            academic_year="2026-2027",
            subject_id="subject-math",
            component_id="component-math-geometry",
        ),
        TeacherSubjectRegistration(
            registration_id="registration-002",
            owner_id="teacher-001",
            academic_year="2026-2027",
            subject_id="subject-math",
            component_id="component-math-geometry",
        ),
    )

    scopes = build_service(
        registrations
    ).list_scopes(
        owner_id="teacher-001",
        academic_year="2026-2027",
    )

    assert len(scopes) == 1


def test_inactive_registration_is_not_exposed():
    registration = TeacherSubjectRegistration(
        registration_id="registration-001",
        owner_id="teacher-001",
        academic_year="2026-2027",
        subject_id="subject-math",
        component_id="component-math-geometry",
        status=(
            TeacherSubjectRegistrationStatus.INACTIVE
        ),
    )

    scopes = build_service(
        (registration,)
    ).list_scopes(
        owner_id="teacher-001",
        academic_year="2026-2027",
    )

    assert scopes == ()


def test_missing_component_is_not_exposed():
    registration = TeacherSubjectRegistration(
        registration_id="registration-001",
        owner_id="teacher-001",
        academic_year="2026-2027",
        subject_id="subject-math",
        component_id="component-missing",
    )

    scopes = build_service(
        (registration,)
    ).list_scopes(
        owner_id="teacher-001",
        academic_year="2026-2027",
    )

    assert scopes == ()
