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
    Math6MvpWorkflowError,
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

    workflow.create_blueprint(
        blueprint_code="M6-BP-001",
        title="Ma trận Toán 6 tối thiểu",
        question_count=2,
        total_score="2",
        topic_codes=("M6-NATURAL-NUMBERS",),
    )
    workflow.submit_blueprint("M6-BP-001")
    assert len(workflow.blueprint_review_queue) == 1
    blueprint = workflow.review_blueprint(
        "M6-BP-001", role=ADMIN, approve=True
    )
    assert blueprint.review_status == APPROVED
    assert blueprint.locked
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
