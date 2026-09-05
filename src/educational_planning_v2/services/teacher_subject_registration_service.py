from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    SubjectComponentPolicy,
)
from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
)
from educational_planning_v2.repositories.subject_catalog_repository import (
    SubjectCatalogRepository,
)


@dataclass(frozen=True)
class TeacherSubjectRegistrationValidationResult:
    registration: TeacherSubjectRegistration


class TeacherSubjectRegistrationService:
    def __init__(
        self,
        *,
        catalog_repository: SubjectCatalogRepository,
    ) -> None:
        if catalog_repository is None:
            raise ValueError(
                "catalog_repository must not be None"
            )

        self._catalog_repository = (
            catalog_repository
        )

    def validate_registration(
        self,
        *,
        registration: TeacherSubjectRegistration,
    ) -> TeacherSubjectRegistrationValidationResult:
        if not isinstance(
            registration,
            TeacherSubjectRegistration,
        ):
            raise TypeError(
                "registration must be "
                "TeacherSubjectRegistration"
            )

        subject = (
            self._catalog_repository.get_subject(
                subject_id=registration.subject_id
            )
        )

        if subject is None:
            raise ValueError(
                "subject does not exist"
            )

        if subject.status is not CatalogStatus.ACTIVE:
            raise ValueError(
                "subject must be ACTIVE"
            )

        component_id = (
            registration.component_id
        )

        if (
            subject.component_policy
            is SubjectComponentPolicy.NONE
        ):
            if component_id is not None:
                raise ValueError(
                    "subject does not allow components"
                )

            return (
                TeacherSubjectRegistrationValidationResult(
                    registration=registration
                )
            )

        # V14B6K_MATH_BLANK_COMPONENT_VALID
        if (
            subject.component_policy
            is SubjectComponentPolicy.REQUIRED
            and component_id is None
            and subject.code.strip().upper() != "MATH"
        ):
            raise ValueError(
                "subject requires a component"
            )

        if component_id is None:
            return (
                TeacherSubjectRegistrationValidationResult(
                    registration=registration
                )
            )

        component = (
            self._catalog_repository.get_component(
                component_id=component_id
            )
        )

        if component is None:
            raise ValueError(
                "component does not exist"
            )

        if (
            component.status
            is not CatalogStatus.ACTIVE
        ):
            raise ValueError(
                "component must be ACTIVE"
            )

        if (
            component.subject_id
            != subject.subject_id
        ):
            raise ValueError(
                "component does not belong "
                "to subject"
            )

        return (
            TeacherSubjectRegistrationValidationResult(
                registration=registration
            )
        )
