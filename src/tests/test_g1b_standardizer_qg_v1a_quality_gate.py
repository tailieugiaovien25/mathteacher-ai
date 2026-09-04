from types import SimpleNamespace

from document_intelligence.contracts import DocumentField
from document_intelligence.validation import ValidationStatus
from document_standardization.lesson_plan_standardization_quality_gate import (
    LessonPlanStandardizationQualityGate,
    QualityGateStatus,
)


def _canonical(**overrides):
    values = dict(
        class_name="6A1",
        curriculum_period=12,
        lesson_title="Fractions",
        drafting_date="01/09/2026",
        teaching_date="02/09/2026",
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _validated(**statuses):
    defaults = {
        DocumentField.CLASS_NAME: ValidationStatus.ACCEPTED,
        DocumentField.CURRICULUM_PERIOD: ValidationStatus.ACCEPTED,
        DocumentField.LESSON_TITLE: ValidationStatus.ACCEPTED,
        DocumentField.DRAFTING_DATE: ValidationStatus.ACCEPTED,
        DocumentField.TEACHING_DATE: ValidationStatus.ACCEPTED,
    }
    defaults.update(statuses)
    items = []
    for field, status in defaults.items():
        items.append(
            SimpleNamespace(
                proposal=SimpleNamespace(field=field),
                status=status,
            )
        )
    return SimpleNamespace(proposals=tuple(items))


def test_all_canonical_matches_pass():
    result = LessonPlanStandardizationQualityGate().evaluate(
        canonical_context=_canonical(),
        validated_analysis=_validated(),
        context_result=SimpleNamespace(unresolved_fields=()),
        standardization_report={"warnings": []},
    )
    assert result.status is QualityGateStatus.PASS
    assert result.fail_count == 0
    assert result.review_count == 0


def test_conflict_fails_gate():
    result = LessonPlanStandardizationQualityGate().evaluate(
        canonical_context=_canonical(),
        validated_analysis=_validated(**{DocumentField.CLASS_NAME: ValidationStatus.CONFLICT}),
        context_result=SimpleNamespace(unresolved_fields=()),
        standardization_report={},
    )
    assert result.status is QualityGateStatus.FAIL
    assert result.conflict_count == 1


def test_unresolved_standardization_field_fails_gate():
    result = LessonPlanStandardizationQualityGate().evaluate(
        canonical_context=_canonical(),
        validated_analysis=_validated(),
        context_result=SimpleNamespace(unresolved_fields=("lesson_title",)),
        standardization_report={},
    )
    assert result.status is QualityGateStatus.FAIL
    assert any(item.code == "STANDARDIZATION_UNRESOLVED" for item in result.criteria)


def test_warning_requires_review_without_failing():
    result = LessonPlanStandardizationQualityGate().evaluate(
        canonical_context=_canonical(),
        validated_analysis=_validated(),
        context_result=SimpleNamespace(unresolved_fields=()),
        standardization_report={"warnings": ["integrity warning"]},
    )
    assert result.status is QualityGateStatus.REVIEW
    assert result.fail_count == 0
    assert result.review_count == 1


def test_missing_canonical_value_is_review_not_fake_pass():
    result = LessonPlanStandardizationQualityGate().evaluate(
        canonical_context=_canonical(drafting_date=None),
        validated_analysis=_validated(),
        context_result=SimpleNamespace(unresolved_fields=()),
        standardization_report={},
    )
    assert result.status is QualityGateStatus.REVIEW
    assert any(item.code == "CANONICAL_VALUE_MISSING" for item in result.criteria)


def test_unverified_field_requires_review():
    result = LessonPlanStandardizationQualityGate().evaluate(
        canonical_context=_canonical(),
        validated_analysis=_validated(**{DocumentField.LESSON_TITLE: ValidationStatus.UNVERIFIED}),
        context_result=SimpleNamespace(unresolved_fields=()),
        standardization_report={},
    )
    assert result.status is QualityGateStatus.REVIEW
    assert any(item.code == "NOT_FULLY_VERIFIED" for item in result.criteria)


def test_quality_gate_module_has_no_mutating_runtime_dependencies():
    import inspect
    import document_standardization.lesson_plan_standardization_quality_gate as module

    text = inspect.getsource(module)
    forbidden = (
        "lesson_plan_configuration_runtime_bridge",
        "supabase",
        "save_handler",
        "merge(",
        "standardize(",
        "Document(",
    )
    assert all(token not in text for token in forbidden)
