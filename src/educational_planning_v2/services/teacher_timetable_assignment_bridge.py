from __future__ import annotations

from dataclasses import dataclass
import unicodedata
from typing import Iterable

from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
)
from educational_planning_v2.services.teacher_timetable_subject_scope_service import (
    TeacherTimetableSubjectScope,
)


@dataclass(frozen=True)
class TeacherTimetableAssignmentOption:
    assignment_id: str
    class_id: str
    subject_id: str
    subject_name: str
    component_id: str | None
    component_name: str | None

    @property
    def selection_key(
        self,
    ) -> tuple[str, str, str | None]:
        return (
            self.class_id,
            self.subject_id,
            self.component_id,
        )


class TeacherTimetableAssignmentBridge:
    """
    Bridge canonical teacher subject registrations
    to existing TeachingAssignment records.

    Canonical catalog remains authoritative for
    subject/component choices.

    TeachingAssignment remains authoritative for
    the class + assignment_id relationship.
    """

    _LEGACY_COMPONENT_ALIASES = {
        "xstk": "sxtk",
        "xac suat thong ke": "sxtk",
        "xac suat va thong ke": "sxtk",
    }

    @classmethod
    def _normalized_text(
        cls,
        value: str | None,
    ) -> str:
        if not value:
            return ""

        text = unicodedata.normalize(
            "NFD",
            value.strip(),
        )

        text = "".join(
            character
            for character in text
            if unicodedata.category(character)
            != "Mn"
        )

        text = text.replace(
            "\u0111",
            "d",
        ).replace(
            "\u0110",
            "D",
        )

        return " ".join(
            text.casefold().split()
        )

    @classmethod
    def _normalized_component(
        cls,
        value: str | None,
    ) -> str:
        normalized = cls._normalized_text(
            value
        )

        return cls._LEGACY_COMPONENT_ALIASES.get(
            normalized,
            normalized,
        )

    @classmethod
    def _assignment_matches_scope(
        cls,
        *,
        assignment: TeachingAssignment,
        scope: TeacherTimetableSubjectScope,
    ) -> bool:
        assignment_subject = cls._normalized_text(
            assignment.subject_ref
        )

        assignment_component = (
            cls._normalized_component(
                assignment.component_ref
            )
        )

        scope_subject = cls._normalized_text(
            scope.subject_name
        )

        scope_component = (
            cls._normalized_component(
                scope.component_name
            )
        )

        # ----------------------------------------------------
        # CANONICAL RULE
        #
        # TeachingAssignment owns:
        #     Class + Subject + assignment_id
        #
        # TeacherSubjectRegistration / ADMIN Catalog owns:
        #     allowed Components
        #
        # Therefore, when the assignment explicitly names
        # the parent subject (for example "Toan"), an old
        # component_ref must NOT restrict the canonical
        # component choices shown in the timetable.
        # ----------------------------------------------------

        if assignment_subject == scope_subject:
            return True

        # ----------------------------------------------------
        # LEGACY COMPONENT-LEVEL ASSIGNMENT
        #
        # Very old records may store the component itself in
        # subject_ref, for example:
        #
        #     subject_ref = "Hinh hoc"
        #
        # In that case the assignment genuinely represents
        # only that component, so keep the restriction.
        # ----------------------------------------------------

        if (
            scope.component_id is not None
            and assignment_subject
            == scope_component
        ):
            return True

        # ----------------------------------------------------
        # LEGACY FALLBACK
        #
        # Some records may have a non-canonical subject_ref
        # but a useful component_ref. Only use this fallback
        # when the parent subject itself did not already
        # match.
        # ----------------------------------------------------

        if (
            scope.component_id is not None
            and assignment_component
            and assignment_component
            == scope_component
        ):
            return True

        return False

    def build_options(
        self,
        *,
        assignments: Iterable[
            TeachingAssignment
        ],
        subject_scopes: Iterable[
            TeacherTimetableSubjectScope
        ],
    ) -> tuple[
        TeacherTimetableAssignmentOption,
        ...
    ]:
        assignments = tuple(
            assignments
        )
        subject_scopes = tuple(
            subject_scopes
        )

        result: list[
            TeacherTimetableAssignmentOption
        ] = []

        seen: set[
            tuple[str, str, str | None]
        ] = set()

        for assignment in assignments:
            for scope in subject_scopes:
                if not self._assignment_matches_scope(
                    assignment=assignment,
                    scope=scope,
                ):
                    continue

                option = (
                    TeacherTimetableAssignmentOption(
                        assignment_id=(
                            assignment.assignment_id
                        ),
                        class_id=assignment.class_id,
                        subject_id=scope.subject_id,
                        subject_name=(
                            scope.subject_name
                        ),
                        component_id=(
                            scope.component_id
                        ),
                        component_name=(
                            scope.component_name
                        ),
                    )
                )

                if option.selection_key in seen:
                    continue

                seen.add(
                    option.selection_key
                )

                result.append(
                    option
                )

        return tuple(result)
