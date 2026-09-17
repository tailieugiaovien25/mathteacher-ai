from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from assessment_generation_v2.services.assessment_foundation import (
    AssessmentConfig,
)
from assessment_generation_v2.services.canonical_assessment_selection_service import (
    CanonicalAssessmentSelection,
)
from assessment_generation_v2.services.math6_mvp_workflow import (
    ADMIN,
    InMemoryMath6MvpWorkflow,
    Math6AssessmentBlueprint,
    Math6AssessmentConfig,
    Math6AssessmentExam,
    Math6AssessmentQuestion,
    Math6Blueprint,
    Math6Exam,
    Math6MvpWorkflowError,
    Math6PublishedAssessmentPackage,
    Math6PublishedPackage,
    Math6Question,
)


def _config() -> Math6AssessmentConfig:
    return Math6AssessmentConfig(
        config_code="M6-COMPAT",
        title="Math 6 compatibility",
        academic_year="2026-2027",
        semester="HK1",
        test_type="MIDTERM",
        duration_minutes=90,
        total_score="1",
        variant_count=1,
    )


def _published_package():
    workflow = InMemoryMath6MvpWorkflow()
    question = workflow.create_question(
        question_code="M6-Q-001",
        stem="Tính 1 + 1.",
        answer="2",
        score="1",
        topic_code="M6-NUMBER",
        cognitive_level="KNOW",
    )
    workflow.submit_question(question.question_code)
    workflow.review_question(question.question_code, role=ADMIN, approve=True)
    workflow.lock_question(question.question_code, role=ADMIN)
    workflow.create_blueprint(
        blueprint_code="M6-BP-COMPAT",
        title="Math 6 compatibility blueprint",
        assessment_config=_config(),
        question_count=1,
        total_score="1",
        topic_codes=("M6-NUMBER",),
    )
    workflow.submit_blueprint("M6-BP-COMPAT")
    workflow.review_blueprint("M6-BP-COMPAT", role=ADMIN, approve=True)
    exam = workflow.generate_exam(
        exam_code="M6-EXAM-COMPAT",
        title="Math 6 compatibility exam",
        blueprint_code="M6-BP-COMPAT",
    )
    workflow.submit_exam(exam.exam_code)
    workflow.review_exam(exam.exam_code, role=ADMIN, approve=True)
    return workflow.publish_exam(exam.exam_code, role=ADMIN, variant_code="101")


def test_math6_legacy_class_identities_and_config_constructor_are_unchanged() -> None:
    assert Math6AssessmentQuestion is Math6Question
    assert Math6AssessmentBlueprint is Math6Blueprint
    assert Math6AssessmentExam is Math6Exam
    assert Math6PublishedAssessmentPackage is Math6PublishedPackage
    config = _config()
    assert config.config_code == "M6-COMPAT"
    assert str(config.total_score) == "1"


def test_math6_config_projection_is_additive_and_canonical() -> None:
    legacy = _config()
    canonical = legacy.to_canonical()
    assert type(canonical) is AssessmentConfig
    assert canonical.subject_code == "MATH"
    assert canonical.grade_level == 6
    assert canonical.config_code == legacy.config_code
    assert canonical.total_score == legacy.total_score


def test_existing_math6_grade_six_guard_remains_unchanged() -> None:
    workflow = InMemoryMath6MvpWorkflow()
    workflow.create_blueprint(
        blueprint_code="M6-BP-GRADE-GUARD",
        title="Grade guard",
        assessment_config=_config(),
        question_count=1,
        total_score="1",
        topic_codes=("M6-NUMBER",),
    )
    grade_seven_selection = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=7,
        program_code="CT2018-MATH",
        selected_topic_codes=("TOPIC-7",),
        selected_requirement_codes=("REQ-7",),
        finalized=True,
    )
    with pytest.raises(Math6MvpWorkflowError, match="must target grade 6"):
        workflow.bind_canonical_coverage(
            "M6-BP-GRADE-GUARD",
            selection=grade_seven_selection,
            assignments=(),
        )


def test_math6_published_snapshot_schema_and_bytes_are_unchanged() -> None:
    package = _published_package()
    expected = (
        b'{"blueprint":{"blueprint_code":"M6-BP-COMPAT",'
        b'"canonical_coverage":null,"config_code":"M6-COMPAT",'
        b'"matrix_authoring":null,"question_count":1,"title":'
        b'"Math 6 compatibility blueprint","topic_codes":["M6-NUMBER"],'
        b'"total_score":"1"},"exam":{"exam_code":"M6-EXAM-COMPAT",'
        b'"review_status":"APPROVED","title":"Math 6 compatibility exam"},'
        b'"grade_level":6,"questions":[{"answer":"2","cognitive_level":'
        b'"KNOW","question_code":"M6-Q-001","score":"1","stem":'
        b'"T\xc3\xadnh 1 + 1.","topic_code":"M6-NUMBER"}],"schema_version":1,'
        b'"subject":"To\xc3\xa1n","variant":{"status":"LOCKED",'
        b'"variant_code":"101"}}'
    )
    actual = package.snapshot_json.encode("utf-8")
    assert package.snapshot()["schema_version"] == 1
    assert package.snapshot()["grade_level"] == 6
    assert actual == expected
    assert package.snapshot_hash == sha256(expected).hexdigest()
