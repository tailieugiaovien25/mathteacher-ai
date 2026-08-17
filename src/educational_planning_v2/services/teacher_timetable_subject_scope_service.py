from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
)
from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistrationStatus,
)
from educational_planning_v2.repositories.subject_catalog_repository import (
    SubjectCatalogRepository,
)
from educational_planning_v2.repositories.teacher_subject_registration_repository import (
    TeacherSubjectRegistrationRepository,
)


@dataclass(frozen=True)
class TeacherTimetableSubjectScope:
    subject_id: str
    subject_name: str
    component_id: str | None
    component_name: str | None

    @property
    def selection_key(
        self,
    ) -> tuple[str, str | None]:
        return (
            self.subject_id,
            self.component_id,
        )


class TeacherTimetableSubjectScopeService:
    def __init__(
        self,
        *,
        catalog_repository: SubjectCatalogRepository,
        registration_repository: (
            TeacherSubjectRegistrationRepository
        ),
    ) -> None:
        if catalog_repository is None:
            raise ValueError(
                "catalog_repository must not be None"
            )

        if registration_repository is None:
            raise ValueError(
                "registration_repository must not be None"
            )

        self._catalog_repository = (
            catalog_repository
        )
        self._registration_repository = (
            registration_repository
        )

        self._performance_audit: dict[str, float] = {}

    def list_scopes(
        self,
        *,
        owner_id: str,
        academic_year: str,
    ) -> tuple[
        TeacherTimetableSubjectScope,
        ...
    ]:
        _perf_step = perf_counter()

        registrations = (
            self._registration_repository.list_registrations(
                owner_id=owner_id,
                academic_year=academic_year,
                status=(
                    TeacherSubjectRegistrationStatus.ACTIVE
                ),
            )
        )

        self._performance_audit[
            "registration_load_ms"
        ] = (
            perf_counter() - _perf_step
        ) * 1000

        _perf_step = perf_counter()

        subjects = (
            self._catalog_repository.list_subjects(
                status=CatalogStatus.ACTIVE,
            )
        )

        self._performance_audit[
            "subjects_load_ms"
        ] = (
            perf_counter() - _perf_step
        ) * 1000

        _perf_step = perf_counter()

        components = (
            self._catalog_repository.list_components(
                status=CatalogStatus.ACTIVE,
            )
        )

        self._performance_audit[
            "components_load_ms"
        ] = (
            perf_counter() - _perf_step
        ) * 1000

        subject_by_id = {
            item.subject_id: item
            for item in subjects
        }

        component_by_id = {
            item.component_id: item
            for item in components
        }

        result: list[
            TeacherTimetableSubjectScope
        ] = []

        seen: set[
            tuple[str, str | None]
        ] = set()

        for registration in registrations:
            subject = subject_by_id.get(
                registration.subject_id
            )

            if subject is None:
                continue

            component = None

            if registration.component_id is not None:
                component = component_by_id.get(
                    registration.component_id
                )

                if component is None:
                    continue

                if (
                    component.subject_id
                    != subject.subject_id
                ):
                    continue

            key = (
                subject.subject_id,
                (
                    None
                    if component is None
                    else component.component_id
                ),
            )

            if key in seen:
                continue

            seen.add(key)

            result.append(
                TeacherTimetableSubjectScope(
                    subject_id=subject.subject_id,
                    subject_name=subject.name,
                    component_id=(
                        None
                        if component is None
                        else component.component_id
                    ),
                    component_name=(
                        None
                        if component is None
                        else component.name
                    ),
                )
            )

        return tuple(result)

    @property
    def performance_audit(
        self,
    ) -> dict[str, float]:
        return dict(
            self._performance_audit
        )
