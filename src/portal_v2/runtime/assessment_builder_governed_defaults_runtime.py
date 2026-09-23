"""Read-only runtime for governed Mathematics 6-9 builder defaults.

The runtime reads approved assessment settings plus their governed profile
structure from Supabase and delegates all validation/selection rules to
AssessmentBuilderGovernedDefaultsService.

It performs no writes and does not infer an assessment type from names/codes.
The selected assessment type is supplied explicitly and must match the approved
setting row. Ambiguous or missing matches fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from assessment_generation_v2.services.assessment_builder_governed_defaults_service import (
    AssessmentBuilderGovernedDefaults,
    AssessmentBuilderGovernedDefaultsService,
    GovernedAssessmentSectionSnapshot,
    GovernedAssessmentSettingSnapshot,
    GovernedCognitiveAllocationSnapshot,
)


class AssessmentBuilderGovernedDefaultsRuntimeError(RuntimeError):
    """Raised when governed defaults cannot be loaded safely."""


def _data(response: object) -> object:
    if isinstance(response, Mapping):
        return response.get("data")
    return getattr(response, "data", None)


def _rows(response: object) -> list[dict[str, Any]]:
    data = _data(response)

    if data is None:
        return []

    if isinstance(data, Mapping):
        return [dict(data)]

    if not isinstance(data, list):
        raise AssessmentBuilderGovernedDefaultsRuntimeError(
            "Supabase response must contain a list"
        )

    if any(
        not isinstance(row, Mapping)
        for row in data
    ):
        raise AssessmentBuilderGovernedDefaultsRuntimeError(
            "Supabase response contains an invalid row"
        )

    return [
        dict(row)
        for row in data
    ]


def _relation(
    value: object,
    field: str,
) -> dict[str, Any]:
    if isinstance(value, list):
        if len(value) != 1:
            raise AssessmentBuilderGovernedDefaultsRuntimeError(
                f"{field} must contain exactly one related row"
            )
        value = value[0]

    if not isinstance(value, Mapping):
        raise AssessmentBuilderGovernedDefaultsRuntimeError(
            f"{field} relation is invalid"
        )

    return dict(value)


@dataclass(frozen=True, slots=True)
class AssessmentBuilderGovernedDefaultsRuntimeResult:
    defaults: AssessmentBuilderGovernedDefaults

    @property
    def setting_version_id(self) -> str:
        return (
            self.defaults.setting.setting_version_id
        )

    @property
    def profile_code(self) -> str:
        return self.defaults.setting.profile_code


class AssessmentBuilderGovernedDefaultsRuntime:
    """Authenticated read boundary for approved builder defaults."""

    def __init__(
        self,
        *,
        client: Any,
        user_id: str,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        try:
            normalized_user_id = str(
                UUID(str(user_id).strip())
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                "user_id must be a valid UUID"
            ) from error

        self._client = client
        self._user_id = normalized_user_id
        self._service = (
            AssessmentBuilderGovernedDefaultsService()
        )

    def load_defaults(
        self,
        *,
        subject_code: str,
        assessment_type_code: str,
        grade_level: int,
        academic_year: str,
        semester_number: int,
    ) -> AssessmentBuilderGovernedDefaultsRuntimeResult:
        settings = self._list_visible_approved_settings(
            subject_code=subject_code,
            assessment_type_code=assessment_type_code,
            grade_level=grade_level,
            academic_year=academic_year,
            semester_number=semester_number,
        )

        try:
            setting = self._service.resolve_unique_setting(
                settings=settings,
                subject_code=subject_code,
                assessment_type_code=assessment_type_code,
                grade_level=grade_level,
                academic_year=academic_year,
                semester_number=semester_number,
            )
        except Exception as error:
            raise AssessmentBuilderGovernedDefaultsRuntimeError(
                str(error)
            ) from error

        sections = self._list_profile_sections(
            profile_code=setting.profile_code,
        )
        allocations = (
            self._list_profile_level_allocations(
                profile_code=setting.profile_code,
            )
        )

        try:
            defaults = self._service.build(
                setting=setting,
                sections=sections,
                cognitive_allocations=allocations,
            )
        except Exception as error:
            raise AssessmentBuilderGovernedDefaultsRuntimeError(
                str(error)
            ) from error

        return (
            AssessmentBuilderGovernedDefaultsRuntimeResult(
                defaults=defaults,
            )
        )

    def _list_visible_approved_settings(
        self,
        *,
        subject_code: str,
        assessment_type_code: str,
        grade_level: int,
        academic_year: str,
        semester_number: int,
    ) -> tuple[
        GovernedAssessmentSettingSnapshot,
        ...,
    ]:
        normalized_subject = str(subject_code).strip().upper()
        normalized_assessment_type = str(
            assessment_type_code
        ).strip().upper()
        normalized_academic_year = str(
            academic_year
        ).strip()

        try:
            normalized_grade = int(grade_level)
            normalized_semester = int(semester_number)
        except (TypeError, ValueError) as error:
            raise AssessmentBuilderGovernedDefaultsRuntimeError(
                "governed assessment scope is invalid"
            ) from error

        try:
            response = (
                self._client
                .table(
                    "assessment_exam_setting_versions"
                )
                .select(
                    "setting_version_id,profile_code,"
                    "subject_code,assessment_type_code,grade_level,academic_year,"
                    "semester_number,duration_minutes,"
                    "total_score,review_status,locked_at,"
                    "assessment_exam_setting_sets!inner("
                    "owner_user_id,visibility,lifecycle_status)"
                )
                .eq(
                    "review_status",
                    "APPROVED",
                )
                .not_
                .is_(
                    "locked_at",
                    "null",
                )
                .eq(
                    "assessment_exam_setting_sets.lifecycle_status",
                    "ACTIVE",
                )
                .eq(
                    "subject_code",
                    normalized_subject,
                )
                .eq(
                    "assessment_type_code",
                    normalized_assessment_type,
                )
                .eq(
                    "grade_level",
                    normalized_grade,
                )
                .eq(
                    "academic_year",
                    normalized_academic_year,
                )
                .eq(
                    "semester_number",
                    normalized_semester,
                )
                .order(
                    "created_at",
                    desc=True,
                )
                .execute()
            )
        except Exception as error:
            raise AssessmentBuilderGovernedDefaultsRuntimeError(
                "governed assessment settings could not be queried safely "
                "for the explicit assessment type"
            ) from error

        result: list[
            GovernedAssessmentSettingSnapshot
        ] = []

        for row in _rows(response):
            row_subject = str(
                row.get("subject_code") or ""
            ).strip().upper()
            row_assessment_type = str(
                row.get("assessment_type_code") or ""
            ).strip().upper()
            row_academic_year = str(
                row.get("academic_year") or ""
            ).strip()

            try:
                row_grade = int(row.get("grade_level"))
                row_semester = int(row.get("semester_number"))
            except (TypeError, ValueError):
                continue

            if (
                row_subject != normalized_subject
                or row_assessment_type
                != normalized_assessment_type
                or row_grade != normalized_grade
                or row_academic_year
                != normalized_academic_year
                or row_semester != normalized_semester
            ):
                continue

            setting_set = _relation(
                row.get(
                    "assessment_exam_setting_sets"
                ),
                "assessment_exam_setting_sets",
            )

            owner_id = str(
                setting_set.get(
                    "owner_user_id"
                )
                or ""
            ).strip()

            visibility = str(
                setting_set.get(
                    "visibility"
                )
                or ""
            ).strip().upper()

            if (
                owner_id != self._user_id
                and visibility != "SHARED"
            ):
                continue

            result.append(
                GovernedAssessmentSettingSnapshot(
                    setting_version_id=row.get(
                        "setting_version_id"
                    ),
                    profile_code=row.get(
                        "profile_code"
                    ),
                    subject_code=row.get(
                        "subject_code"
                    ),
                    assessment_type_code=row.get(
                        "assessment_type_code"
                    ),
                    grade_level=row.get(
                        "grade_level"
                    ),
                    academic_year=row.get(
                        "academic_year"
                    ),
                    semester_number=row.get(
                        "semester_number"
                    ),
                    duration_minutes=row.get(
                        "duration_minutes"
                    ),
                    total_score=Decimal(
                        str(
                            row.get(
                                "total_score"
                            )
                        )
                    ),
                )
            )

        return tuple(result)

    def _list_profile_sections(
        self,
        *,
        profile_code: str,
    ) -> tuple[
        GovernedAssessmentSectionSnapshot,
        ...,
    ]:
        response = (
            self._client
            .table(
                "assessment_profile_sections"
            )
            .select(
                "section_code,question_type_code,"
                "sequence_number,question_count,"
                "response_count,section_score"
            )
            .eq(
                "profile_code",
                profile_code,
            )
            .order(
                "sequence_number",
            )
            .execute()
        )

        return tuple(
            GovernedAssessmentSectionSnapshot(
                section_code=row.get(
                    "section_code"
                ),
                question_type_code=row.get(
                    "question_type_code"
                ),
                question_count=row.get(
                    "question_count"
                ),
                response_count=row.get(
                    "response_count"
                ),
                section_score=Decimal(
                    str(
                        row.get(
                            "section_score"
                        )
                    )
                ),
            )
            for row in _rows(response)
        )

    def _list_profile_level_allocations(
        self,
        *,
        profile_code: str,
    ) -> tuple[
        GovernedCognitiveAllocationSnapshot,
        ...,
    ]:
        response = (
            self._client
            .table(
                "assessment_profile_level_allocations"
            )
            .select(
                "cognitive_level_code,"
                "target_score,target_percentage"
            )
            .eq(
                "profile_code",
                profile_code,
            )
            .order(
                "cognitive_level_code",
            )
            .execute()
        )

        return tuple(
            GovernedCognitiveAllocationSnapshot(
                cognitive_level_code=row.get(
                    "cognitive_level_code"
                ),
                target_score=Decimal(
                    str(
                        row.get(
                            "target_score"
                        )
                    )
                ),
                target_percentage=Decimal(
                    str(
                        row.get(
                            "target_percentage"
                        )
                    )
                ),
            )
            for row in _rows(response)
        )
