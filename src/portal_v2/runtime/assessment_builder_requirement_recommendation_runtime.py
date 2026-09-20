"""Read-only runtime for exact PPCT-backed YCCĐ recommendations.

This boundary composes two authenticated Supabase RPCs:

1. PPCT source row -> reviewed textbook LESSON
2. reviewed textbook LESSON -> ACCEPT-only learning requirement

It never writes to Supabase, never performs title/fuzzy matching, and never
applies recommendations to the teacher's final selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID


BRIDGE_RPC_NAME = "get_assessment_ppct_textbook_lessons"
RECOMMENDATION_RPC_NAME = (
    "get_textbook_unit_requirement_recommendations"
)
RECOMMENDATION_STATUS = "EXACT_REVIEWED_RECOMMENDATION"


class AssessmentBuilderRequirementRecommendationRuntimeError(
    RuntimeError
):
    """Raised when exact recommendation evidence cannot be trusted."""


def _rows(
    response: object,
    *,
    rpc_name: str,
) -> list[dict[str, Any]]:
    data = (
        response.get("data")
        if isinstance(response, Mapping)
        else getattr(response, "data", None)
    )

    if not isinstance(data, list):
        raise (
            AssessmentBuilderRequirementRecommendationRuntimeError(
                f"{rpc_name} must return a row list"
            )
        )

    if any(
        not isinstance(row, Mapping)
        for row in data
    ):
        raise (
            AssessmentBuilderRequirementRecommendationRuntimeError(
                f"{rpc_name} returned an invalid row"
            )
        )

    return [
        dict(row)
        for row in data
    ]


def _required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise (
            AssessmentBuilderRequirementRecommendationRuntimeError(
                f"{field_name} must be str"
            )
        )

    normalized = " ".join(
        value.strip().split()
    )

    if not normalized:
        raise (
            AssessmentBuilderRequirementRecommendationRuntimeError(
                f"{field_name} must not be empty"
            )
        )

    return normalized


def _optional_text(
    value: object,
    *,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise (
            AssessmentBuilderRequirementRecommendationRuntimeError(
                f"{field_name} must be str or None"
            )
        )

    normalized = " ".join(
        value.strip().split()
    )

    return normalized or None


def _positive_int(
    value: object,
    *,
    field_name: str,
) -> int:
    if isinstance(value, bool):
        raise (
            AssessmentBuilderRequirementRecommendationRuntimeError(
                f"{field_name} must be a positive integer"
            )
        )

    try:
        normalized = int(value)
    except (TypeError, ValueError) as error:
        raise (
            AssessmentBuilderRequirementRecommendationRuntimeError(
                f"{field_name} must be a positive integer"
            )
        ) from error

    if normalized <= 0:
        raise (
            AssessmentBuilderRequirementRecommendationRuntimeError(
                f"{field_name} must be a positive integer"
            )
        )

    return normalized


def _uuid_text(
    value: object,
    *,
    field_name: str,
) -> str:
    try:
        return str(
            UUID(str(value).strip())
        )
    except (TypeError, ValueError) as error:
        raise (
            AssessmentBuilderRequirementRecommendationRuntimeError(
                f"{field_name} must be a valid UUID"
            )
        ) from error


@dataclass(frozen=True, slots=True)
class AssessmentPpctLessonMatch:
    textbook_unit_id: str
    lesson_number: int
    lesson_title: str
    first_period: int
    last_period: int


@dataclass(frozen=True, slots=True)
class AssessmentRequirementRecommendation:
    textbook_unit_id: str
    requirement_code: str
    candidate_id: str
    review_id: str


@dataclass(frozen=True, slots=True)
class AssessmentBuilderRequirementRecommendationResult:
    source_id: str
    source_version: str
    subject_grade: str
    sub_subject: str | None
    period_from: int
    period_to: int
    lessons: tuple[AssessmentPpctLessonMatch, ...]
    recommendations: tuple[
        AssessmentRequirementRecommendation,
        ...
    ]
    status: str = RECOMMENDATION_STATUS

    @property
    def textbook_unit_ids(self) -> tuple[str, ...]:
        return tuple(
            lesson.textbook_unit_id
            for lesson in self.lessons
        )

    @property
    def requirement_codes(self) -> tuple[str, ...]:
        seen: set[str] = set()
        result: list[str] = []

        for recommendation in self.recommendations:
            code = recommendation.requirement_code
            if code in seen:
                continue
            seen.add(code)
            result.append(code)

        return tuple(result)


class AssessmentBuilderRequirementRecommendationRuntime:
    """Authenticated, read-only exact recommendation boundary."""

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

    @property
    def user_id(self) -> str:
        return self._user_id

    def recommend(
        self,
        *,
        source_id: str,
        source_version: str,
        subject_grade: str,
        sub_subject: str | None,
        period_from: int,
        period_to: int,
    ) -> AssessmentBuilderRequirementRecommendationResult:
        normalized_source_id = _required_text(
            source_id,
            field_name="source_id",
        )
        normalized_source_version = _required_text(
            source_version,
            field_name="source_version",
        )
        normalized_subject_grade = _required_text(
            subject_grade,
            field_name="subject_grade",
        )
        normalized_sub_subject = _optional_text(
            sub_subject,
            field_name="sub_subject",
        )
        normalized_period_from = _positive_int(
            period_from,
            field_name="period_from",
        )
        normalized_period_to = _positive_int(
            period_to,
            field_name="period_to",
        )

        if normalized_period_to < normalized_period_from:
            raise (
                AssessmentBuilderRequirementRecommendationRuntimeError(
                    "period_to must be greater than or equal to period_from"
                )
            )

        lessons = self._load_lessons(
            source_id=normalized_source_id,
            source_version=normalized_source_version,
            subject_grade=normalized_subject_grade,
            sub_subject=normalized_sub_subject,
            period_from=normalized_period_from,
            period_to=normalized_period_to,
        )

        recommendations = self._load_recommendations(
            lessons=lessons,
        )

        return AssessmentBuilderRequirementRecommendationResult(
            source_id=normalized_source_id,
            source_version=normalized_source_version,
            subject_grade=normalized_subject_grade,
            sub_subject=normalized_sub_subject,
            period_from=normalized_period_from,
            period_to=normalized_period_to,
            lessons=lessons,
            recommendations=recommendations,
        )

    def _load_lessons(
        self,
        *,
        source_id: str,
        source_version: str,
        subject_grade: str,
        sub_subject: str | None,
        period_from: int,
        period_to: int,
    ) -> tuple[AssessmentPpctLessonMatch, ...]:
        try:
            response = self._client.rpc(
                BRIDGE_RPC_NAME,
                {
                    "target_source_id": source_id,
                    "target_payload_version": source_version,
                    "target_subject_grade": subject_grade,
                    "target_sub_subject": sub_subject or "",
                    "target_period_from": period_from,
                    "target_period_to": period_to,
                },
            ).execute()
        except Exception as error:
            raise (
                AssessmentBuilderRequirementRecommendationRuntimeError(
                    "PPCT lesson bridge RPC failed"
                )
            ) from error

        rows = _rows(
            response,
            rpc_name=BRIDGE_RPC_NAME,
        )

        if not rows:
            raise (
                AssessmentBuilderRequirementRecommendationRuntimeError(
                    "no reviewed textbook lessons exist for the PPCT scope"
                )
            )

        result: list[AssessmentPpctLessonMatch] = []
        seen_ids: set[str] = set()

        for row in rows:
            textbook_unit_id = _required_text(
                row.get("textbook_unit_id"),
                field_name="textbook_unit_id",
            )

            if textbook_unit_id in seen_ids:
                raise (
                    AssessmentBuilderRequirementRecommendationRuntimeError(
                        "PPCT lesson bridge returned duplicate textbook lessons"
                    )
                )

            seen_ids.add(textbook_unit_id)

            lesson_number = _positive_int(
                row.get("lesson_number"),
                field_name="lesson_number",
            )
            lesson_title = _required_text(
                row.get("lesson_title"),
                field_name="lesson_title",
            )
            first_period = _positive_int(
                row.get("first_period"),
                field_name="first_period",
            )
            last_period = _positive_int(
                row.get("last_period"),
                field_name="last_period",
            )

            if last_period < first_period:
                raise (
                    AssessmentBuilderRequirementRecommendationRuntimeError(
                        "lesson period range is invalid"
                    )
                )

            if (
                first_period < period_from
                or last_period > period_to
            ):
                raise (
                    AssessmentBuilderRequirementRecommendationRuntimeError(
                        "lesson period range falls outside requested PPCT scope"
                    )
                )

            result.append(
                AssessmentPpctLessonMatch(
                    textbook_unit_id=textbook_unit_id,
                    lesson_number=lesson_number,
                    lesson_title=lesson_title,
                    first_period=first_period,
                    last_period=last_period,
                )
            )

        return tuple(result)

    def _load_recommendations(
        self,
        *,
        lessons: tuple[AssessmentPpctLessonMatch, ...],
    ) -> tuple[
        AssessmentRequirementRecommendation,
        ...
    ]:
        textbook_unit_ids = tuple(
            lesson.textbook_unit_id
            for lesson in lessons
        )

        try:
            response = self._client.rpc(
                RECOMMENDATION_RPC_NAME,
                {
                    "target_textbook_unit_ids": list(
                        textbook_unit_ids
                    )
                },
            ).execute()
        except Exception as error:
            raise (
                AssessmentBuilderRequirementRecommendationRuntimeError(
                    "requirement recommendation RPC failed"
                )
            ) from error

        rows = _rows(
            response,
            rpc_name=RECOMMENDATION_RPC_NAME,
        )

        if not rows:
            raise (
                AssessmentBuilderRequirementRecommendationRuntimeError(
                    "no exact reviewed requirement recommendations exist"
                )
            )

        lesson_order = {
            lesson_id: index
            for index, lesson_id in enumerate(
                textbook_unit_ids
            )
        }

        parsed: list[
            AssessmentRequirementRecommendation
        ] = []
        seen_pairs: set[tuple[str, str]] = set()

        for row in rows:
            textbook_unit_id = _required_text(
                row.get("textbook_unit_id"),
                field_name="textbook_unit_id",
            )
            requirement_code = _required_text(
                row.get("requirement_code"),
                field_name="requirement_code",
            )

            if textbook_unit_id not in lesson_order:
                raise (
                    AssessmentBuilderRequirementRecommendationRuntimeError(
                        "recommendation references a lesson outside PPCT scope"
                    )
                )

            pair = (
                textbook_unit_id,
                requirement_code,
            )

            if pair in seen_pairs:
                raise (
                    AssessmentBuilderRequirementRecommendationRuntimeError(
                        "duplicate lesson/requirement recommendation returned"
                    )
                )

            seen_pairs.add(pair)

            parsed.append(
                AssessmentRequirementRecommendation(
                    textbook_unit_id=textbook_unit_id,
                    requirement_code=requirement_code,
                    candidate_id=_uuid_text(
                        row.get("candidate_id"),
                        field_name="candidate_id",
                    ),
                    review_id=_uuid_text(
                        row.get("review_id"),
                        field_name="review_id",
                    ),
                )
            )

        recommendation_lesson_ids = {
            row.textbook_unit_id
            for row in parsed
        }

        missing_lessons = [
            lesson_id
            for lesson_id in textbook_unit_ids
            if lesson_id not in recommendation_lesson_ids
        ]

        if missing_lessons:
            raise (
                AssessmentBuilderRequirementRecommendationRuntimeError(
                    "one or more PPCT lessons have no exact reviewed "
                    "requirement recommendations"
                )
            )

        parsed.sort(
            key=lambda row: (
                lesson_order[row.textbook_unit_id],
                row.requirement_code,
            )
        )

        return tuple(parsed)
