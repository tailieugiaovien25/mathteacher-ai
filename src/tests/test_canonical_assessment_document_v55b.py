from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from assessment_generation_v2.documents import (
    CanonicalAssessmentDocumentBuilder,
    CanonicalAssessmentDocumentError,
)


EXAM_VERSION_ID = "11111111-1111-4111-8111-111111111111"
VARIANT_ID = "22222222-2222-4222-8222-222222222222"


def _exam() -> dict[str, object]:
    return {
        "exam_version_id": EXAM_VERSION_ID,
        "exam_title": "Đề kiểm tra giữa học kỳ I",
        "subject_code": "MATH",
        "grade_level": 6,
        "total_score": 10,
        "duration_minutes": 90,
    }


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_schema_version": 2,
        "publication": {
            "publication_id": (
                "33333333-3333-4333-8333-333333333333"
            ),
            "published_at": "2026-08-25T00:00:00Z",
        },
        "exam": _exam(),
        "blueprint": {
            "blueprint_version_id": (
                "44444444-4444-4444-8444-444444444444"
            ),
            "blueprint_name": "Ma trận Toán 6",
            "sections": [
                {
                    "section_code": "MCQ",
                    "section_name": "Trắc nghiệm",
                    "sequence_number": 1,
                }
            ],
            "matrix_cells": [
                {
                    "blueprint_cell_id": (
                        "55555555-5555-4555-8555-555555555555"
                    ),
                    "section_code": "MCQ",
                    "section_name": "Trắc nghiệm",
                    "topic_code": "M6_NUMBER",
                    "topic_name": "Số và Đại số",
                    "domain_code": "NUMBER",
                    "topic_sequence_number": 1,
                    "cognitive_level_code": "KNOW",
                    "cognitive_level_name": "Nhận biết",
                    "cognitive_sequence_number": 1,
                    "question_type_code": "MCQ",
                    "question_type_name": "Trắc nghiệm",
                    "question_count": 1,
                    "response_count": 1,
                    "target_score": 0.25,
                    "sequence_number": 1,
                    "specification_note": "",
                }
            ],
            "requirement_links": [
                {
                    "requirement_code": "M6_REQ_001",
                    "requirement_text": (
                        "Nhận biết được tập hợp số tự nhiên."
                    ),
                    "requirement_version_number": 1,
                    "source_locator": "CTGDPT 2018",
                    "topic_code": "M6_NUMBER",
                    "topic_name": "Số và Đại số",
                    "domain_code": "NUMBER",
                    "coverage_role": "PRIMARY",
                    "target_question_count": 1,
                    "target_score": 0.25,
                    "sequence_number": 1,
                    "specification_note": "",
                    "competencies": [
                        {
                            "competency_code": "MATH_REASONING",
                            "competency_name": (
                                "Tư duy và lập luận toán học"
                            ),
                        }
                    ],
                }
            ],
        },
        "questions": [],
    }


def _variant() -> dict[str, object]:
    return {
        "variant_id": VARIANT_ID,
        "variant_code": "101",
        "variant_hash": "a" * 64,
    }


def _student() -> dict[str, object]:
    return {
        "package_schema_version": 1,
        "package_type": "STUDENT_EXAM",
        "variant": _variant(),
        "exam": _exam(),
        "questions": [
            {
                "display_number": 1,
                "assigned_score": 0.25,
                "question_type_code": "MCQ",
                "prompt_text": "Số tự nhiên nhỏ nhất là số nào?",
                "options": [
                    {
                        "option_code": "A",
                        "option_text": "0",
                        "sequence_number": 1,
                    }
                ],
                "statements": [],
            }
        ],
    }


def _answers() -> dict[str, object]:
    return {
        "package_schema_version": 1,
        "package_type": "ANSWER_KEY",
        "variant": _variant(),
        "exam": _exam(),
        "answers": [
            {
                "display_number": 1,
                "assigned_score": 0.25,
                "question_type_code": "MCQ",
                "correct_options": ["A"],
                "statement_answers": [],
                "answer": {},
            }
        ],
    }


def _scoring() -> dict[str, object]:
    return {
        "package_schema_version": 1,
        "package_type": "SCORING_GUIDE",
        "variant": _variant(),
        "exam": _exam(),
        "scoring_items": [
            {
                "display_number": 1,
                "assigned_score": 0.25,
                "question_type_code": "MCQ",
                "correct_options": ["A"],
                "statements": [],
                "answer": {},
                "solutions": [],
            }
        ],
    }


def _build():
    return CanonicalAssessmentDocumentBuilder().build(
        snapshot_document=_snapshot(),
        student_exam_payload=_student(),
        answer_key_payload=_answers(),
        scoring_guide_payload=_scoring(),
    )


def test_builds_six_template_independent_blocks() -> None:
    document = _build()

    assert document.metadata
    assert len(document.matrix) == 1
    assert len(document.specification) == 1
    assert len(document.questions) == 1
    assert len(document.answer_key) == 1
    assert len(document.scoring_guide) == 1


def test_matrix_uses_frozen_snapshot_labels() -> None:
    row = _build().matrix[0]

    assert row["topic_name"] == "Số và Đại số"
    assert row["cognitive_level_name"] == "Nhận biết"
    assert row["target_score"] == 0.25


def test_specification_exposes_topic_level_matrix_allocation() -> None:
    row = _build().specification[0]

    assert row["requirement_code"] == "M6_REQ_001"
    assert row["competencies"][0]["competency_code"] == (
        "MATH_REASONING"
    )
    assert row["allocation_scope"] == "TOPIC"
    assert row["topic_matrix_allocations"][0][
        "cognitive_level_code"
    ] == "KNOW"
    assert "matrix_allocations" not in row


def test_metadata_preserves_publication_exam_blueprint_variant() -> None:
    metadata = _build().metadata

    assert metadata["publication"]
    assert metadata["exam"]["exam_version_id"] == EXAM_VERSION_ID
    assert metadata["blueprint"]["blueprint_name"] == (
        "Ma trận Toán 6"
    )
    assert metadata["variant"]["variant_id"] == VARIANT_ID


def test_rejects_snapshot_schema_one() -> None:
    snapshot = _snapshot()
    snapshot["snapshot_schema_version"] = 1

    with pytest.raises(
        CanonicalAssessmentDocumentError,
        match="schema 2",
    ):
        CanonicalAssessmentDocumentBuilder().build(
            snapshot_document=snapshot,
            student_exam_payload=_student(),
            answer_key_payload=_answers(),
            scoring_guide_payload=_scoring(),
        )


def test_rejects_wrong_package_type() -> None:
    answers = _answers()
    answers["package_type"] = "STUDENT_EXAM"

    with pytest.raises(
        CanonicalAssessmentDocumentError,
        match="ANSWER_KEY",
    ):
        CanonicalAssessmentDocumentBuilder().build(
            snapshot_document=_snapshot(),
            student_exam_payload=_student(),
            answer_key_payload=answers,
            scoring_guide_payload=_scoring(),
        )


def test_rejects_mixed_variants() -> None:
    answers = _answers()
    answers["variant"] = {
        **_variant(),
        "variant_id": (
            "99999999-9999-4999-8999-999999999999"
        ),
    }

    with pytest.raises(
        CanonicalAssessmentDocumentError,
        match="different variants",
    ):
        CanonicalAssessmentDocumentBuilder().build(
            snapshot_document=_snapshot(),
            student_exam_payload=_student(),
            answer_key_payload=answers,
            scoring_guide_payload=_scoring(),
        )


def test_rejects_mismatched_exam_version() -> None:
    student = _student()
    student["exam"] = {
        **_exam(),
        "exam_version_id": (
            "88888888-8888-4888-8888-888888888888"
        ),
    }

    with pytest.raises(
        CanonicalAssessmentDocumentError,
        match="does not match snapshot",
    ):
        CanonicalAssessmentDocumentBuilder().build(
            snapshot_document=_snapshot(),
            student_exam_payload=student,
            answer_key_payload=_answers(),
            scoring_guide_payload=_scoring(),
        )


def test_rejects_different_question_sequences() -> None:
    scoring = _scoring()
    scoring["scoring_items"][0]["display_number"] = 2

    with pytest.raises(
        CanonicalAssessmentDocumentError,
        match="sequences differ",
    ):
        CanonicalAssessmentDocumentBuilder().build(
            snapshot_document=_snapshot(),
            student_exam_payload=_student(),
            answer_key_payload=_answers(),
            scoring_guide_payload=scoring,
        )


def test_canonical_data_is_deeply_immutable() -> None:
    document = _build()

    with pytest.raises(TypeError):
        document.metadata["exam"]["exam_title"] = "Changed"

    with pytest.raises(TypeError):
        document.matrix[0]["topic_name"] = "Changed"

    with pytest.raises(TypeError):
        document.specification[0][
            "topic_matrix_allocations"
        ][0]["target_score"] = 99


def test_contract_is_frozen() -> None:
    document = _build()

    with pytest.raises(FrozenInstanceError):
        document.schema_version = 2


def test_model_has_no_output_template_terms() -> None:
    from pathlib import Path

    source = Path(
        "src/assessment_generation_v2/documents/"
        "canonical_assessment_document.py"
    ).read_text(encoding="utf-8-sig")

    forbidden = (
        "DOCX",
        "PDF",
        "template_code",
        "template_version",
        "DIEN_BIEN",
        "streamlit",
        "supabase",
        "portal_v2",
    )

    for value in forbidden:
        assert value not in source
