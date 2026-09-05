import pytest

from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    Subject,
    SubjectComponent,
    SubjectComponentPolicy,
)
from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
)
from educational_planning_v2.services.teacher_subject_registration_service import (
    TeacherSubjectRegistrationService,
)


class FakeSubjectCatalogRepository:
    def __init__(
        self,
        *,
        subjects=(),
        components=(),
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


def _registration(
    *,
    subject_id="subject-math",
    component_id=None,
):
    return TeacherSubjectRegistration(
        registration_id="registration-001",
        owner_id="teacher-001",
        academic_year="2026-2027",
        subject_id=subject_id,
        component_id=component_id,
    )


def _subject(
    *,
    subject_id="subject-math",
    policy=SubjectComponentPolicy.OPTIONAL,
    status=CatalogStatus.ACTIVE,
):
    return Subject(
        subject_id=subject_id,
        code=subject_id.upper(),
        name=subject_id,
        component_policy=policy,
        status=status,
    )


def _component(
    *,
    component_id="component-math-algebra",
    subject_id="subject-math",
    status=CatalogStatus.ACTIVE,
):
    return SubjectComponent(
        component_id=component_id,
        subject_id=subject_id,
        code=component_id.upper(),
        name=component_id,
        status=status,
    )


def _service(
    *,
    subjects=(),
    components=(),
):
    return TeacherSubjectRegistrationService(
        catalog_repository=(
            FakeSubjectCatalogRepository(
                subjects=subjects,
                components=components,
            )
        )
    )


def test_optional_subject_allows_subject_level_registration():
    service = _service(
        subjects=(
            _subject(),
        )
    )

    result = service.validate_registration(
        registration=_registration()
    )

    assert result.registration.subject_id == (
        "subject-math"
    )

    assert (
        result.registration.component_id
        is None
    )


def test_optional_subject_allows_component_level_registration():
    service = _service(
        subjects=(
            _subject(),
        ),
        components=(
            _component(),
        ),
    )

    result = service.validate_registration(
        registration=_registration(
            component_id=(
                "component-math-algebra"
            )
        )
    )

    assert (
        result.registration.component_id
        == "component-math-algebra"
    )


def test_none_policy_rejects_component():
    service = _service(
        subjects=(
            _subject(
                subject_id="subject-literature",
                policy=SubjectComponentPolicy.NONE,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="does not allow components",
    ):
        service.validate_registration(
            registration=_registration(
                subject_id="subject-literature",
                component_id=(
                    "component-anything"
                ),
            )
        )


def test_none_policy_allows_subject_level_registration():
    service = _service(
        subjects=(
            _subject(
                subject_id="subject-literature",
                policy=SubjectComponentPolicy.NONE,
            ),
        ),
    )

    result = service.validate_registration(
        registration=_registration(
            subject_id="subject-literature"
        )
    )

    assert result.registration.is_subject_level


def test_required_policy_rejects_missing_component():
    service = _service(
        subjects=(
            _subject(
                policy=(
                    SubjectComponentPolicy.REQUIRED
                )
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="requires a component",
    ):
        service.validate_registration(
            registration=_registration()
        )


def test_required_policy_accepts_valid_component():
    service = _service(
        subjects=(
            _subject(
                policy=(
                    SubjectComponentPolicy.REQUIRED
                )
            ),
        ),
        components=(
            _component(),
        ),
    )

    result = service.validate_registration(
        registration=_registration(
            component_id=(
                "component-math-algebra"
            )
        )
    )

    assert result.registration.is_component_level


def test_unknown_subject_is_rejected():
    service = _service()

    with pytest.raises(
        ValueError,
        match="subject does not exist",
    ):
        service.validate_registration(
            registration=_registration()
        )


def test_inactive_subject_is_rejected():
    service = _service(
        subjects=(
            _subject(
                status=CatalogStatus.INACTIVE,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="subject must be ACTIVE",
    ):
        service.validate_registration(
            registration=_registration()
        )


def test_unknown_component_is_rejected():
    service = _service(
        subjects=(
            _subject(),
        ),
    )

    with pytest.raises(
        ValueError,
        match="component does not exist",
    ):
        service.validate_registration(
            registration=_registration(
                component_id=(
                    "component-missing"
                )
            )
        )


def test_inactive_component_is_rejected():
    service = _service(
        subjects=(
            _subject(),
        ),
        components=(
            _component(
                status=CatalogStatus.INACTIVE,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="component must be ACTIVE",
    ):
        service.validate_registration(
            registration=_registration(
                component_id=(
                    "component-math-algebra"
                )
            )
        )


def test_component_from_other_subject_is_rejected():
    service = _service(
        subjects=(
            _subject(),
            _subject(
                subject_id="subject-art",
            ),
        ),
        components=(
            _component(
                component_id=(
                    "component-art-music"
                ),
                subject_id="subject-art",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="does not belong to subject",
    ):
        service.validate_registration(
            registration=_registration(
                subject_id="subject-math",
                component_id=(
                    "component-art-music"
                ),
            )
        )


def test_registration_type_is_validated():
    service = _service()

    with pytest.raises(
        TypeError,
        match="registration",
    ):
        service.validate_registration(
            registration="subject-math"
        )


def test_service_requires_catalog_repository():
    with pytest.raises(
        ValueError,
        match="catalog_repository",
    ):
        TeacherSubjectRegistrationService(
            catalog_repository=None
        )


def test_math_required_policy_allows_blank_component():
    service = _service(
        subjects=(
            Subject(
                subject_id="subject-math",
                code="MATH",
                name="To?n",
                component_policy=SubjectComponentPolicy.REQUIRED,
            ),
        ),
    )

    result = service.validate_registration(
        registration=_registration(
            subject_id="subject-math",
            component_id=None,
        )
    )

    assert result.registration.component_id is None


def test_non_math_required_policy_still_rejects_blank_component():
    service = _service(
        subjects=(
            Subject(
                subject_id="subject-english",
                code="FOREIGN_LANGUAGE_1",
                name="Ti?ng Anh",
                component_policy=SubjectComponentPolicy.REQUIRED,
            ),
        ),
    )

    try:
        service.validate_registration(
            registration=_registration(
                subject_id="subject-english",
                component_id=None,
            )
        )
    except ValueError as exc:
        assert str(exc) == "subject requires a component"
    else:
        raise AssertionError(
            "required non-math component must be rejected"
        )
