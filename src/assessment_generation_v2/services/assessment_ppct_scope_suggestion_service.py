"""Automatic PPCT scope suggestion for Math 6-9 assessment authoring.

The service is deterministic and fail-closed:
- it receives canonical PPCTRow values already loaded by system runtime,
- resolves exactly one Math/grade PPCT scope,
- delegates period-boundary resolution to AssessmentPpctScopeResolver,
- returns evidence for UI presentation.

It owns no persistence, Supabase access, Streamlit state, or AI behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from assessment_generation_v2.services.assessment_ppct_scope_resolver import (
    AssessmentPpctScopeResolution,
    AssessmentPpctScopeResolutionError,
    AssessmentPpctScopeResolver,
)
from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from educational_planning_v2.services.ppct_scope_catalog import (
    PPCTScopeCatalog,
    PPCTScopeOption,
)


class AssessmentPpctScopeSuggestionError(ValueError):
    """Raised when automatic PPCT scope suggestion cannot be trusted."""


@dataclass(frozen=True, slots=True)
class AssessmentPpctScopeSuggestion:
    grade_level: int
    subject_name: str
    subject_grade: str
    sub_subject: str | None
    assessment_type: str
    semester: int
    period_from: int
    period_to: int
    marker_period: int
    marker_title: str
    scope_rows: tuple[PPCTRow, ...]
    evidence_source: str = "PPCT"
    suggestion_status: str = "SUGGESTED_FROM_PPCT"

    @property
    def selection_key(
        self,
    ) -> tuple[int, str, int, str, str | None]:
        return (
            self.grade_level,
            self.assessment_type,
            self.semester,
            self.subject_grade,
            self.sub_subject,
        )


class AssessmentPpctScopeSuggestionService:
    """Turn teacher assessment selection into a PPCT-backed scope suggestion."""

    def __init__(
        self,
        *,
        resolver: AssessmentPpctScopeResolver | None = None,
        scope_catalog: PPCTScopeCatalog | None = None,
    ) -> None:
        self._resolver = (
            resolver
            if resolver is not None
            else AssessmentPpctScopeResolver()
        )
        self._scope_catalog = (
            scope_catalog
            if scope_catalog is not None
            else PPCTScopeCatalog()
        )

    def suggest(
        self,
        *,
        ppct_rows: tuple[PPCTRow, ...],
        grade_level: int,
        assessment_type: str,
        semester: int,
        subject_name: str = "Toán",
        sub_subject: str | None = None,
    ) -> AssessmentPpctScopeSuggestion:
        grade = self._grade_level(grade_level)
        subject = self._required_text(
            subject_name,
            "subject_name",
        )
        normalized_sub_subject = self._optional_text(
            sub_subject
        )

        self._validate_ppct_rows(ppct_rows)

        options = self._scope_catalog.build_options(
            rows=ppct_rows,
        )

        option = self._resolve_scope_option(
            options=options,
            subject_name=subject,
            grade_level=grade,
            sub_subject=normalized_sub_subject,
        )

        scoped_rows = tuple(
            row
            for row in ppct_rows
            if (
                self._fold(row.subject_grade)
                == self._fold(option.subject_grade)
                and self._fold_optional(row.sub_subject)
                == self._fold_optional(option.sub_subject)
            )
        )

        if not scoped_rows:
            raise AssessmentPpctScopeSuggestionError(
                "resolved PPCT scope contains no rows"
            )

        try:
            resolution = self._resolver.resolve(
                rows=scoped_rows,
                assessment_type=assessment_type,
                semester=semester,
            )
        except AssessmentPpctScopeResolutionError as error:
            raise AssessmentPpctScopeSuggestionError(
                str(error)
            ) from error

        return self._to_suggestion(
            grade_level=grade,
            subject_name=subject,
            resolution=resolution,
        )

    @classmethod
    def _resolve_scope_option(
        cls,
        *,
        options: tuple[PPCTScopeOption, ...],
        subject_name: str,
        grade_level: int,
        sub_subject: str | None,
    ) -> PPCTScopeOption:
        expected_subject_grade = (
            f"{subject_name.strip()} {grade_level}"
        )

        subject_matches = tuple(
            option
            for option in options
            if (
                cls._fold(option.subject_grade)
                == cls._fold(expected_subject_grade)
            )
        )

        if not subject_matches:
            raise AssessmentPpctScopeSuggestionError(
                "no PPCT scope matches "
                f"{expected_subject_grade!r}"
            )

        if sub_subject is not None:
            subject_matches = tuple(
                option
                for option in subject_matches
                if (
                    cls._fold_optional(option.sub_subject)
                    == cls._fold_optional(sub_subject)
                )
            )

            if not subject_matches:
                raise AssessmentPpctScopeSuggestionError(
                    "no PPCT sub-subject scope matches "
                    f"{expected_subject_grade!r} / "
                    f"{sub_subject!r}"
                )

        if len(subject_matches) != 1:
            raise AssessmentPpctScopeSuggestionError(
                "PPCT scope is ambiguous; exactly one "
                "subject-grade/sub-subject scope is required"
            )

        return subject_matches[0]

    @staticmethod
    def _to_suggestion(
        *,
        grade_level: int,
        subject_name: str,
        resolution: AssessmentPpctScopeResolution,
    ) -> AssessmentPpctScopeSuggestion:
        return AssessmentPpctScopeSuggestion(
            grade_level=grade_level,
            subject_name=subject_name,
            subject_grade=resolution.subject_grade,
            sub_subject=resolution.sub_subject,
            assessment_type=resolution.assessment_type,
            semester=resolution.semester,
            period_from=resolution.period_from,
            period_to=resolution.period_to,
            marker_period=resolution.marker_period,
            marker_title=resolution.marker_title,
            scope_rows=resolution.scope_rows,
        )

    @staticmethod
    def _validate_ppct_rows(
        rows: tuple[PPCTRow, ...],
    ) -> None:
        if not isinstance(rows, tuple):
            raise TypeError(
                "ppct_rows must be a tuple"
            )

        if not rows:
            raise AssessmentPpctScopeSuggestionError(
                "PPCT rows must not be empty"
            )

        if not all(
            isinstance(row, PPCTRow)
            for row in rows
        ):
            raise TypeError(
                "ppct_rows must contain PPCTRow values"
            )

    @staticmethod
    def _grade_level(
        value: object,
    ) -> int:
        if isinstance(value, bool):
            raise AssessmentPpctScopeSuggestionError(
                "grade_level must be one of 6, 7, 8, 9"
            )

        try:
            grade = int(value)
        except (TypeError, ValueError) as error:
            raise AssessmentPpctScopeSuggestionError(
                "grade_level must be one of 6, 7, 8, 9"
            ) from error

        if grade not in {6, 7, 8, 9}:
            raise AssessmentPpctScopeSuggestionError(
                "grade_level must be one of 6, 7, 8, 9"
            )

        return grade

    @staticmethod
    def _required_text(
        value: object,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = " ".join(
            value.strip().split()
        )

        if not normalized:
            raise AssessmentPpctScopeSuggestionError(
                f"{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                "sub_subject must be str or None"
            )

        normalized = " ".join(
            value.strip().split()
        )

        return normalized or None

    @staticmethod
    def _fold_optional(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = (
            AssessmentPpctScopeSuggestionService
            ._fold(value)
        )

        return normalized or None

    @staticmethod
    def _fold(
        value: object,
    ) -> str:
        text = str(value or "").strip().casefold()
        text = unicodedata.normalize(
            "NFD",
            text,
        )
        text = "".join(
            character
            for character in text
            if unicodedata.category(character) != "Mn"
        )
        text = text.replace("đ", "d")

        return " ".join(text.split())