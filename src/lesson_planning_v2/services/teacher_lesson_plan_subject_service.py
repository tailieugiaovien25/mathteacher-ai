from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
)
from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignmentStatus,
)
from educational_planning_v2.repositories.subject_catalog_repository import (
    SubjectCatalogRepository,
)
from educational_planning_v2.repositories.teacher_subject_assignment_repository import (
    TeacherSubjectAssignmentRepository,
)


@dataclass(frozen=True)
class TeacherLessonPlanSubject:
    subject_id: str
    code: str
    name: str
    display_order: int = 0


class TeacherLessonPlanSubjectService:
    """
    Resolve the active subjects available to a teacher for lesson plans.

    Subject availability comes from teacher-subject assignments.
    Subject metadata comes from the canonical subject catalog.

    The service owns no persistence, UI, Supabase implementation,
    textbook names, or fixed subject list.
    """

    def __init__(
        self,
        *,
        assignment_repository: TeacherSubjectAssignmentRepository,
        subject_repository: SubjectCatalogRepository,
    ) -> None:
        self._assignment_repository = assignment_repository
        self._subject_repository = subject_repository

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized

    def list_subjects(
        self,
        *,
        teacher_id: str,
        academic_year: str,
    ) -> tuple[TeacherLessonPlanSubject, ...]:
        normalized_teacher_id = self._required_text(
            teacher_id,
            "teacher_id",
        )
        normalized_academic_year = self._required_text(
            academic_year,
            "academic_year",
        )

        assignments = (
            self._assignment_repository.list_assignments(
                teacher_id=normalized_teacher_id,
                academic_year=normalized_academic_year,
                status=TeacherSubjectAssignmentStatus.ACTIVE,
            )
        )

        subjects_by_id: dict[
            str,
            TeacherLessonPlanSubject,
        ] = {}

        for assignment in assignments:
            subject_id = assignment.subject_id

            if subject_id in subjects_by_id:
                continue

            subject = self._subject_repository.get_subject(
                subject_id=subject_id
            )

            if subject is None:
                continue

            if subject.status is not CatalogStatus.ACTIVE:
                continue

            subjects_by_id[subject_id] = (
                TeacherLessonPlanSubject(
                    subject_id=subject.subject_id,
                    code=subject.code,
                    name=subject.name,
                    display_order=subject.display_order,
                )
            )

        return tuple(
            sorted(
                subjects_by_id.values(),
                key=lambda item: (
                    item.display_order,
                    item.name.casefold(),
                    item.subject_id,
                ),
            )
        )
