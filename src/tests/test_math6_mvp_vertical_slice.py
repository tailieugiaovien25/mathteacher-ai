from __future__ import annotations

import sys
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assessment_generation_v2.services.math6_mvp_workflow import (
    ADMIN,
    APPROVED,
    PENDING_REVIEW,
    InMemoryMath6MvpWorkflow,
    Math6AssessmentConfig,
    Math6MvpWorkflowError,
)
from assessment_generation_v2.services.blueprint_requirement_link_service import (
    BlueprintRequirementAssignment,
)
from assessment_generation_v2.services.canonical_assessment_selection_service import (
    CanonicalAssessmentSelection,
)
from portal_v2.ui.math6_mvp_demo_streamlit import (
    parse_question_import_json,
    sample_import_json,
    sample_question_rows,
    workflow_status,
)


def _seed_questions(workflow: InMemoryMath6MvpWorkflow) -> None:
    imported = workflow.import_questions(
        (
            {
                "question_code": "M6-NAT-001",
                "stem": "Tính 27 + 35.",
                "answer": "62",
                "score": "1",
                "topic_code": "M6-NATURAL-NUMBERS",
                "cognitive_level": "KNOW",
            },
            {
                "question_code": "M6-NAT-002",
                "stem": "Tìm x biết x - 18 = 24.",
                "answer": "x = 42",
                "score": "1",
                "topic_code": "M6-NATURAL-NUMBERS",
                "cognitive_level": "UNDERSTAND",
            },
        )
    )
    assert len(imported) == 2
    edited = workflow.edit_question(
        "M6-NAT-002",
        stem="Tìm số tự nhiên x biết x - 18 = 24.",
    )
    assert edited.stem.startswith("Tìm số tự nhiên")
    for code in ("M6-NAT-001", "M6-NAT-002"):
        submitted = workflow.submit_question(code)
        assert submitted.review_status == PENDING_REVIEW
        approved = workflow.review_question(
            code, role=ADMIN, approve=True
        )
        assert approved.review_status == APPROVED
        assert workflow.lock_question(code, role=ADMIN).locked


def test_math6_mvp_vertical_slice_reaches_locked_zip() -> None:
    workflow = InMemoryMath6MvpWorkflow()
    _seed_questions(workflow)
    assert not workflow.question_review_queue

    assessment_config = Math6AssessmentConfig(
        config_code="M6-MIDTERM-2026-HK1",
        title="Kiểm tra giữa học kỳ I - Toán 6",
        academic_year="2026-2027",
        semester="HK1",
        test_type="MIDTERM",
        duration_minutes=90,
        total_score="2",
        variant_count=2,
    )
    workflow.create_blueprint(
        blueprint_code="M6-BP-001",
        title="Ma trận Toán 6 tối thiểu",
        assessment_config=assessment_config,
        question_count=2,
        total_score="2",
        topic_codes=("M6-NATURAL-NUMBERS",),
    )
    canonical_selection = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code="CT2018-MATH",
        selected_topic_codes=("CURR-NODE-MATH-G6-003",),
        selected_requirement_codes=("YCCD-MATH-06-0001",),
        finalized=True,
    )
    workflow.bind_canonical_coverage(
        "M6-BP-001",
        selection=canonical_selection,
        assignments=(
            BlueprintRequirementAssignment(
                requirement_code="YCCD-MATH-06-0001",
                coverage_role="PRIMARY",
                target_question_count=2,
                sequence_number=10,
                target_score="2",
                specification_note="Ph?m vi MVP To?n 6",
            ),
        ),
    )
    workflow.submit_blueprint("M6-BP-001")
    assert len(workflow.blueprint_review_queue) == 1
    blueprint = workflow.review_blueprint(
        "M6-BP-001", role=ADMIN, approve=True
    )
    assert blueprint.review_status == APPROVED
    assert blueprint.locked
    assert blueprint.config_code == assessment_config.config_code
    assert not workflow.blueprint_review_queue

    exam = workflow.generate_exam(
        exam_code="M6-EXAM-001",
        title="Đề kiểm tra Toán 6 tối thiểu",
        blueprint_code="M6-BP-001",
    )
    assert exam.question_codes == ("M6-NAT-001", "M6-NAT-002")
    workflow.submit_exam(exam.exam_code)
    assert len(workflow.exam_review_queue) == 1
    workflow.review_exam(exam.exam_code, role=ADMIN, approve=True)
    published = workflow.publish_exam(
        exam.exam_code, role=ADMIN, variant_code="101"
    )
    assert published.variant_locked
    assert published.snapshot_hash == sha256(
        published.snapshot_json.encode("utf-8")
    ).hexdigest()
    assert (
        published.snapshot()["blueprint"]["config_code"]
        == assessment_config.config_code
    )
    canonical_coverage = published.snapshot()["blueprint"][
        "canonical_coverage"
    ]
    assert canonical_coverage["subject_code"] == "MATH"
    assert canonical_coverage["program_code"] == "CT2018-MATH"
    assert canonical_coverage["topic_codes"] == [
        "CURR-NODE-MATH-G6-003"
    ]
    assert canonical_coverage["requirement_codes"] == [
        "YCCD-MATH-06-0001"
    ]
    assert canonical_coverage["requirement_assignments"][0][
        "target_score"
    ] == "2"

    bundle = workflow.export_zip(exam.exam_code)
    assert bundle.startswith(b"PK")
    with ZipFile(BytesIO(bundle)) as archive:
        assert set(archive.namelist()) == {
            "de-kiem-tra.txt",
            "dap-an-huong-dan-cham.txt",
            "ma-tran-ban-dac-ta.json",
            "snapshot.json",
            "manifest.json",
        }
        exam_text = archive.read("de-kiem-tra.txt").decode("utf-8")
        answer_text = archive.read(
            "dap-an-huong-dan-cham.txt"
        ).decode("utf-8")
    assert "Mã đề: 101" in exam_text
    assert "Câu 2." in exam_text
    assert "x = 42" in answer_text


def test_question_import_is_atomic_and_locked_items_are_immutable() -> None:
    workflow = InMemoryMath6MvpWorkflow()
    with pytest.raises(Math6MvpWorkflowError, match="stem"):
        workflow.import_questions(
            (
                {
                    "question_code": "M6-VALID",
                    "stem": "Một câu hợp lệ",
                    "answer": "1",
                    "score": "1",
                    "topic_code": "M6-TOPIC",
                    "cognitive_level": "KNOW",
                },
                {
                    "question_code": "M6-INVALID",
                    "stem": "",
                    "answer": "2",
                    "score": "1",
                    "topic_code": "M6-TOPIC",
                    "cognitive_level": "KNOW",
                },
            )
        )
    assert not workflow.question_review_queue
    # The valid first row was not partially committed by the failed batch.
    workflow.create_question(
        question_code="M6-VALID",
        stem="Một câu hợp lệ",
        answer="1",
        score="1",
        topic_code="M6-TOPIC",
        cognitive_level="KNOW",
    )
    workflow.submit_question("M6-VALID")
    with pytest.raises(PermissionError, match="ADMIN"):
        workflow.review_question(
            "M6-VALID", role="TEACHER", approve=True
        )
    workflow.review_question("M6-VALID", role=ADMIN, approve=True)
    workflow.lock_question("M6-VALID", role=ADMIN)
    with pytest.raises(Math6MvpWorkflowError, match="editable"):
        workflow.edit_question("M6-VALID", stem="Không được sửa")


def test_export_is_blocked_before_admin_publication() -> None:
    workflow = InMemoryMath6MvpWorkflow()
    with pytest.raises(Math6MvpWorkflowError, match="published snapshot"):
        workflow.export_zip("M6-NOT-PUBLISHED")


def test_streamlit_helpers_parse_json_without_importing_streamlit() -> None:
    parsed = parse_question_import_json(sample_import_json())
    assert parsed == sample_question_rows()
    with pytest.raises(ValueError, match="JSON"):
        parse_question_import_json("not-json")
    with pytest.raises(ValueError, match="mảng JSON"):
        parse_question_import_json("{}")


def test_streamlit_status_tracks_guarded_workflow_transitions() -> None:
    workflow = InMemoryMath6MvpWorkflow()
    assert workflow_status(workflow) == {
        "question_count": 0,
        "question_pending": 0,
        "question_locked": 0,
        "blueprint_count": 0,
        "blueprint_pending": 0,
        "blueprint_ready": False,
        "exam_count": 0,
        "exam_pending": 0,
        "exam_approved": False,
        "published_count": 0,
        "can_create_blueprint": False,
    }
    workflow.import_questions(sample_question_rows())
    for question in workflow.questions:
        workflow.submit_question(question.question_code)
    pending = workflow_status(workflow)
    assert pending["question_pending"] == 2
    assert pending["can_create_blueprint"] is False
    for question in tuple(workflow.question_review_queue):
        workflow.review_question(
            question.question_code, role=ADMIN, approve=True
        )
        workflow.lock_question(question.question_code, role=ADMIN)
    ready = workflow_status(workflow)
    assert ready["question_locked"] == 2
    assert ready["can_create_blueprint"] is True


def test_math6_assessment_config_normalizes_core_fields() -> None:
    config = Math6AssessmentConfig(
        config_code="m6-midterm-2026-hk1",
        title="Math 6 midterm",
        academic_year="2026-2027",
        semester="hk1",
        test_type="midterm",
        duration_minutes="90",
        total_score="10",
        variant_count="2",
    )
    assert config.config_code == "M6-MIDTERM-2026-HK1"
    assert config.title == "Math 6 midterm"
    assert config.academic_year == "2026-2027"
    assert config.semester == "HK1"
    assert config.test_type == "MIDTERM"
    assert config.duration_minutes == 90
    assert str(config.total_score) == "10"
    assert config.variant_count == 2


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("config_code", ""),
        ("title", " "),
        ("academic_year", ""),
        ("semester", ""),
        ("test_type", ""),
        ("duration_minutes", 0),
        ("duration_minutes", "1.5"),
        ("total_score", 0),
        ("variant_count", 0),
        ("variant_count", False),
    ),
)
def test_math6_assessment_config_rejects_invalid_values(
    field_name: str,
    invalid_value: object,
) -> None:
    values = {
        "config_code": "M6-MIDTERM-2026-HK1",
        "title": "Math 6 midterm",
        "academic_year": "2026-2027",
        "semester": "HK1",
        "test_type": "MIDTERM",
        "duration_minutes": 90,
        "total_score": "10",
        "variant_count": 2,
    }
    values[field_name] = invalid_value
    with pytest.raises(Math6MvpWorkflowError):
        Math6AssessmentConfig(**values)



def test_blueprint_requires_config_and_matching_total_score() -> None:
    workflow = InMemoryMath6MvpWorkflow()
    config = Math6AssessmentConfig(
        config_code="M6-FINAL-2026-HK1",
        title="Kiểm tra cuối học kỳ I - Toán 6",
        academic_year="2026-2027",
        semester="HK1",
        test_type="FINAL",
        duration_minutes=90,
        total_score="10",
        variant_count=2,
    )

    with pytest.raises(
        Math6MvpWorkflowError,
        match="assessment_config is required",
    ):
        workflow.create_blueprint(
            blueprint_code="M6-BP-NO-CONFIG",
            title="No config",
            assessment_config=None,
            question_count=2,
            total_score="10",
            topic_codes=("M6-NATURAL-NUMBERS",),
        )

    with pytest.raises(
        Math6MvpWorkflowError,
        match="blueprint total_score must match assessment config",
    ):
        workflow.create_blueprint(
            blueprint_code="M6-BP-MISMATCH",
            title="Score mismatch",
            assessment_config=config,
            question_count=2,
            total_score="9",
            topic_codes=("M6-NATURAL-NUMBERS",),
        )

    blueprint = workflow.create_blueprint(
        blueprint_code="M6-BP-MATCH",
        title="Score match",
        assessment_config=config,
        question_count=2,
        total_score="10",
        topic_codes=("M6-NATURAL-NUMBERS",),
    )

    assert blueprint.config_code == config.config_code
    assert blueprint.total_score == config.total_score



def test_blueprint_canonical_coverage_requires_finalized_matching_selection() -> None:
    workflow = InMemoryMath6MvpWorkflow()
    config = Math6AssessmentConfig(
        config_code="M6-MIDTERM-CANONICAL",
        title="Canonical coverage foundation",
        academic_year="2026-2027",
        semester="HK1",
        test_type="MIDTERM",
        duration_minutes=90,
        total_score="10",
        variant_count=2,
    )
    workflow.create_blueprint(
        blueprint_code="M6-BP-CANONICAL",
        title="Canonical blueprint foundation",
        assessment_config=config,
        question_count=2,
        total_score="10",
        topic_codes=("M6-NATURAL-NUMBERS",),
    )

    editing_selection = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code="CT2018-MATH",
        selected_topic_codes=("CURR-NODE-MATH-G6-003",),
        selected_requirement_codes=("YCCD-MATH-06-0001",),
        finalized=False,
    )
    assignment = BlueprintRequirementAssignment(
        requirement_code="YCCD-MATH-06-0001",
        coverage_role="PRIMARY",
        target_question_count=2,
        sequence_number=10,
        target_score="10",
    )

    with pytest.raises(
        Math6MvpWorkflowError,
        match="must be finalized",
    ):
        workflow.bind_canonical_coverage(
            "M6-BP-CANONICAL",
            selection=editing_selection,
            assignments=(assignment,),
        )

    finalized = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code="CT2018-MATH",
        selected_topic_codes=("CURR-NODE-MATH-G6-003",),
        selected_requirement_codes=("YCCD-MATH-06-0001",),
        finalized=True,
    )
    wrong_assignment = BlueprintRequirementAssignment(
        requirement_code="YCCD-MATH-06-9999",
        coverage_role="PRIMARY",
        target_question_count=2,
        sequence_number=10,
        target_score="10",
    )

    with pytest.raises(
        Math6MvpWorkflowError,
        match="must match selection",
    ):
        workflow.bind_canonical_coverage(
            "M6-BP-CANONICAL",
            selection=finalized,
            assignments=(wrong_assignment,),
        )

    updated = workflow.bind_canonical_coverage(
        "M6-BP-CANONICAL",
        selection=finalized,
        assignments=(assignment,),
    )
    assert updated.canonical_subject_code == "MATH"
    assert updated.canonical_program_code == "CT2018-MATH"
    assert updated.canonical_topic_codes == (
        "CURR-NODE-MATH-G6-003",
    )
    assert updated.canonical_requirement_codes == (
        "YCCD-MATH-06-0001",
    )
    assert updated.requirement_assignments == (assignment,)
