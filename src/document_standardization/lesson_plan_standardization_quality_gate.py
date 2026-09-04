"""Read-only quality gate for standardized lesson-plan artifacts.

G1B_STANDARDIZER_QG_V1A

This module deliberately does not mutate DOCX content, invoke the runtime
configuration bridge, write persistence state, or alter merge behavior.
It only aggregates existing validation/context/standardization evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from document_intelligence.contracts import DocumentField
from document_intelligence.validation import ValidationStatus


class QualityGateStatus(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"


@dataclass(frozen=True)
class QualityGateCriterion:
    field: DocumentField | None
    code: str
    status: QualityGateStatus
    message: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class LessonPlanQualityGateResult:
    status: QualityGateStatus
    criteria: tuple[QualityGateCriterion, ...]
    conflict_count: int
    review_count: int
    fail_count: int

    @property
    def passed(self) -> bool:
        return self.status is QualityGateStatus.PASS


_FIELD_TO_UNRESOLVED_NAME = {
    DocumentField.CLASS_NAME: "class_id",
    DocumentField.CURRICULUM_PERIOD: "curriculum_period",
    DocumentField.LESSON_TITLE: "lesson_title",
    DocumentField.DRAFTING_DATE: "drafting_date",
    DocumentField.TEACHING_DATE: "teaching_date",
}


def _canonical_value(context: Any, field: DocumentField) -> Any:
    if context is None:
        return None
    value_for = getattr(context, "value_for", None)
    if callable(value_for):
        try:
            return value_for(field)
        except Exception:
            pass
    attr = {
        DocumentField.CLASS_NAME: "class_name",
        DocumentField.CURRICULUM_PERIOD: "curriculum_period",
        DocumentField.LESSON_TITLE: "lesson_title",
        DocumentField.DRAFTING_DATE: "drafting_date",
        DocumentField.TEACHING_DATE: "teaching_date",
    }[field]
    if isinstance(context, Mapping):
        return context.get(attr)
    return getattr(context, attr, None)


def _normalize_unresolved(context_result: Any) -> set[str]:
    values = getattr(context_result, "unresolved_fields", ()) if context_result is not None else ()
    return {str(value) for value in (values or ())}


def _validated_items(validated_analysis: Any) -> tuple[Any, ...]:
    values = getattr(validated_analysis, "proposals", ()) if validated_analysis is not None else ()
    return tuple(values or ())


def _status_for_field(validated_analysis: Any, field: DocumentField) -> ValidationStatus | None:
    statuses = []
    for item in _validated_items(validated_analysis):
        proposal = getattr(item, "proposal", None)
        item_field = getattr(proposal, "field", None)
        if item_field is None:
            item_field = getattr(item, "field", None)
        if item_field == field:
            status = getattr(item, "status", None)
            if status is None:
                status = getattr(item, "validation_status", None)
            if isinstance(status, ValidationStatus):
                statuses.append(status)
    if ValidationStatus.CONFLICT in statuses:
        return ValidationStatus.CONFLICT
    if ValidationStatus.ACCEPTED in statuses:
        return ValidationStatus.ACCEPTED
    if ValidationStatus.UNVERIFIED in statuses:
        return ValidationStatus.UNVERIFIED
    return None


def _report_warnings(report: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(report, Mapping):
        return ()
    warnings = report.get("warnings", ())
    if warnings is None:
        return ()
    if isinstance(warnings, str):
        return (warnings,) if warnings.strip() else ()
    if isinstance(warnings, Iterable):
        return tuple(str(item) for item in warnings if str(item).strip())
    return (str(warnings),)


class LessonPlanStandardizationQualityGate:
    """Aggregate existing evidence without changing the document."""

    fields = (
        DocumentField.CLASS_NAME,
        DocumentField.CURRICULUM_PERIOD,
        DocumentField.LESSON_TITLE,
        DocumentField.DRAFTING_DATE,
        DocumentField.TEACHING_DATE,
    )

    def evaluate(
        self,
        *,
        canonical_context: Any,
        validated_analysis: Any,
        context_result: Any,
        standardization_report: Mapping[str, Any] | None,
    ) -> LessonPlanQualityGateResult:
        unresolved = _normalize_unresolved(context_result)
        criteria: list[QualityGateCriterion] = []

        for field in self.fields:
            canonical = _canonical_value(canonical_context, field)
            if canonical in (None, ""):
                criteria.append(
                    QualityGateCriterion(
                        field=field,
                        code="CANONICAL_VALUE_MISSING",
                        status=QualityGateStatus.REVIEW,
                        message="Canonical value is unavailable; this field cannot be fully verified.",
                    )
                )
                continue

            unresolved_name = _FIELD_TO_UNRESOLVED_NAME[field]
            if unresolved_name in unresolved:
                criteria.append(
                    QualityGateCriterion(
                        field=field,
                        code="STANDARDIZATION_UNRESOLVED",
                        status=QualityGateStatus.FAIL,
                        message="Standardization could not resolve this canonical field in the document.",
                        evidence=(unresolved_name,),
                    )
                )
                continue

            validation_status = _status_for_field(validated_analysis, field)
            if validation_status is ValidationStatus.CONFLICT:
                criteria.append(
                    QualityGateCriterion(
                        field=field,
                        code="CANONICAL_CONFLICT",
                        status=QualityGateStatus.FAIL,
                        message="Recognized document value conflicts with canonical lesson context.",
                    )
                )
            elif validation_status is ValidationStatus.ACCEPTED:
                criteria.append(
                    QualityGateCriterion(
                        field=field,
                        code="CANONICAL_MATCH",
                        status=QualityGateStatus.PASS,
                        message="Recognized document value matches canonical lesson context.",
                    )
                )
            else:
                criteria.append(
                    QualityGateCriterion(
                        field=field,
                        code="NOT_FULLY_VERIFIED",
                        status=QualityGateStatus.REVIEW,
                        message="No accepted canonical match was proven for this field.",
                    )
                )

        warnings = _report_warnings(standardization_report)
        if warnings:
            criteria.append(
                QualityGateCriterion(
                    field=None,
                    code="STANDARDIZATION_WARNINGS",
                    status=QualityGateStatus.REVIEW,
                    message="Standardization completed with warnings.",
                    evidence=warnings,
                )
            )

        fail_count = sum(item.status is QualityGateStatus.FAIL for item in criteria)
        review_count = sum(item.status is QualityGateStatus.REVIEW for item in criteria)
        conflict_count = sum(item.code == "CANONICAL_CONFLICT" for item in criteria)

        if fail_count:
            overall = QualityGateStatus.FAIL
        elif review_count:
            overall = QualityGateStatus.REVIEW
        else:
            overall = QualityGateStatus.PASS

        return LessonPlanQualityGateResult(
            status=overall,
            criteria=tuple(criteria),
            conflict_count=conflict_count,
            review_count=review_count,
            fail_count=fail_count,
        )
