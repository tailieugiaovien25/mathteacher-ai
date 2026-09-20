# Read-only presentation enrichment for exact reviewed assessment recommendations.
# This module does not decide curriculum scope and does not write teacher selection.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
    RuntimeError
):
    pass


def _data(response: object) -> object:
    if isinstance(response, Mapping):
        return response.get("data")
    return getattr(response, "data", None)


def _rows(response: object) -> list[dict[str, Any]]:
    value = _data(response)
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    if not isinstance(value, list):
        raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
            "Supabase response must contain a list"
        )
    if any(not isinstance(row, Mapping) for row in value):
        raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
            "Supabase response contains an invalid row"
        )
    return [dict(row) for row in value]


def _text(value: object) -> str:
    return str(value or "").strip()


def _unique(values: tuple[str, ...], *, field: str) -> tuple[str, ...]:
    normalized = tuple(_text(value) for value in values)
    if not normalized or any(not value for value in normalized):
        raise ValueError(f"{field} must contain non-empty values")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field} must not contain duplicates")
    return normalized


@dataclass(frozen=True, slots=True)
class RecommendationLessonPresentation:
    textbook_unit_id: str
    canonical_code: str
    title: str
    chapter_title: str


@dataclass(frozen=True, slots=True)
class RecommendationTopicPresentation:
    topic_code: str
    topic_name: str


@dataclass(frozen=True, slots=True)
class RecommendationRequirementPresentation:
    requirement_code: str
    topic_code: str
    topic_name: str
    requirement_text: str


@dataclass(frozen=True, slots=True)
class AssessmentBuilderRequirementRecommendationPresentationResult:
    lessons: tuple[RecommendationLessonPresentation, ...]
    topics: tuple[RecommendationTopicPresentation, ...]
    requirements: tuple[RecommendationRequirementPresentation, ...]

    @property
    def topic_codes(self) -> tuple[str, ...]:
        return tuple(row.topic_code for row in self.topics)


class AssessmentBuilderRequirementRecommendationPresentationRuntime:
    def __init__(self, *, client: Any) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self._client = client

    def load(
        self,
        *,
        textbook_unit_ids: tuple[str, ...],
        requirement_codes: tuple[str, ...],
    ) -> AssessmentBuilderRequirementRecommendationPresentationResult:
        lesson_ids = _unique(
            textbook_unit_ids,
            field="textbook_unit_ids",
        )
        requirement_ids = _unique(
            requirement_codes,
            field="requirement_codes",
        )

        lesson_rows = _rows(
            self._client
            .table("textbook_units")
            .select(
                "textbook_unit_id,parent_unit_id,unit_type,"
                "canonical_code,title,status"
            )
            .in_("textbook_unit_id", list(lesson_ids))
            .execute()
        )
        lesson_by_id = {
            _text(row.get("textbook_unit_id")): row
            for row in lesson_rows
        }
        if set(lesson_by_id) != set(lesson_ids):
            raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                "one or more recommended SGK lessons have no metadata"
            )

        for lesson_id in lesson_ids:
            row = lesson_by_id[lesson_id]
            if _text(row.get("unit_type")).upper() != "LESSON":
                raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                    "recommended textbook unit is not a LESSON"
                )
            if _text(row.get("status")).upper() != "ACTIVE":
                raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                    "recommended SGK lesson is not ACTIVE"
                )
            if not _text(row.get("title")):
                raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                    "recommended SGK lesson title is missing"
                )

        parent_ids = tuple(
            dict.fromkeys(
                _text(lesson_by_id[lesson_id].get("parent_unit_id"))
                for lesson_id in lesson_ids
                if _text(lesson_by_id[lesson_id].get("parent_unit_id"))
            )
        )
        parent_by_id: dict[str, dict[str, Any]] = {}
        if parent_ids:
            parent_rows = _rows(
                self._client
                .table("textbook_units")
                .select("textbook_unit_id,unit_type,title,status")
                .in_("textbook_unit_id", list(parent_ids))
                .execute()
            )
            parent_by_id = {
                _text(row.get("textbook_unit_id")): row
                for row in parent_rows
            }
            if set(parent_by_id) != set(parent_ids):
                raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                    "one or more SGK lesson chapters have no metadata"
                )

        lessons: list[RecommendationLessonPresentation] = []
        for lesson_id in lesson_ids:
            row = lesson_by_id[lesson_id]
            parent_id = _text(row.get("parent_unit_id"))
            parent = parent_by_id.get(parent_id, {})
            if parent_id:
                if _text(parent.get("unit_type")).upper() != "CHAPTER":
                    raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                        "SGK lesson parent is not a CHAPTER"
                    )
                if _text(parent.get("status")).upper() != "ACTIVE":
                    raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                        "SGK lesson chapter is not ACTIVE"
                    )
                chapter_title = _text(parent.get("title"))
                if not chapter_title:
                    raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                        "SGK lesson chapter title is missing"
                    )
            else:
                chapter_title = ""

            lessons.append(
                RecommendationLessonPresentation(
                    textbook_unit_id=lesson_id,
                    canonical_code=_text(row.get("canonical_code")),
                    title=_text(row.get("title")),
                    chapter_title=chapter_title,
                )
            )

        requirement_rows = _rows(
            self._client
            .table("assessment_learning_requirements")
            .select(
                "requirement_code,topic_code,grade_level,"
                "requirement_text,status"
            )
            .in_("requirement_code", list(requirement_ids))
            .execute()
        )
        requirement_by_code = {
            _text(row.get("requirement_code")): row
            for row in requirement_rows
        }
        if set(requirement_by_code) != set(requirement_ids):
            raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                "one or more recommended YCCD rows have no metadata"
            )

        grade_levels: set[int] = set()
        topic_codes: list[str] = []
        for code in requirement_ids:
            row = requirement_by_code[code]
            if _text(row.get("status")).upper() != "ACTIVE":
                raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                    "recommended YCCD is not ACTIVE"
                )
            requirement_text = _text(row.get("requirement_text"))
            topic_code = _text(row.get("topic_code"))
            if not requirement_text or not topic_code:
                raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                    "recommended YCCD presentation metadata is incomplete"
                )
            try:
                grade_levels.add(int(row.get("grade_level")))
            except (TypeError, ValueError) as error:
                raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                    "recommended YCCD grade is invalid"
                ) from error
            if topic_code not in topic_codes:
                topic_codes.append(topic_code)

        if len(grade_levels) != 1:
            raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                "recommended YCCD rows span multiple grades"
            )
        grade_level = next(iter(grade_levels))

        topic_rows = _rows(
            self._client
            .table("assessment_curriculum_topics")
            .select(
                "topic_code,grade_level,topic_name,status"
            )
            .in_("topic_code", topic_codes)
            .execute()
        )
        topic_by_code = {
            _text(row.get("topic_code")): row
            for row in topic_rows
        }
        if set(topic_by_code) != set(topic_codes):
            raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                "one or more canonical topics have no metadata"
            )

        topics: list[RecommendationTopicPresentation] = []
        for topic_code in topic_codes:
            row = topic_by_code[topic_code]
            if _text(row.get("status")).upper() != "ACTIVE":
                raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                    "recommended canonical topic is not ACTIVE"
                )
            topic_name = _text(row.get("topic_name"))
            if not topic_name:
                raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                    "recommended canonical topic name is missing"
                )
            topic_grade = row.get("grade_level")
            if topic_grade is not None:
                try:
                    normalized_topic_grade = int(topic_grade)
                except (TypeError, ValueError) as error:
                    raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                        "recommended canonical topic grade is invalid"
                    ) from error
                if normalized_topic_grade != grade_level:
                    raise AssessmentBuilderRequirementRecommendationPresentationRuntimeError(
                        "recommended canonical topic grade does not match YCCD grade"
                    )
            topics.append(
                RecommendationTopicPresentation(
                    topic_code=topic_code,
                    topic_name=topic_name,
                )
            )

        requirements = tuple(
            RecommendationRequirementPresentation(
                requirement_code=code,
                topic_code=_text(requirement_by_code[code].get("topic_code")),
                topic_name=_text(
                    topic_by_code[
                        _text(requirement_by_code[code].get("topic_code"))
                    ].get("topic_name")
                ),
                requirement_text=_text(
                    requirement_by_code[code].get("requirement_text")
                ),
            )
            for code in requirement_ids
        )

        return AssessmentBuilderRequirementRecommendationPresentationResult(
            lessons=tuple(lessons),
            topics=tuple(topics),
            requirements=requirements,
        )


# R55C4C14_HUMAN_READABLE_RECOMMENDATION_UI
