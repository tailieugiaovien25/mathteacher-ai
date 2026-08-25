from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from assessment_generation_v2.documents import (
    CanonicalAssessmentDocument,
)
from assessment_generation_v2.renderers import (
    AssessmentTemplateDefinition,
    DynamicAssessmentDocumentRenderer,
    DynamicAssessmentRendererError,
)


def _document() -> CanonicalAssessmentDocument:
    return CanonicalAssessmentDocument(
        schema_version=1,
        metadata={
            "exam": {
                "exam_title": "Đề kiểm tra giữa học kỳ I",
                "subject_code": "MATH",
                "grade_level": 6,
            },
            "variant": {
                "variant_code": "101",
            },
        },
        matrix=(
            {
                "topic_code": "M6_NUMBER",
                "topic_name": "Số và Đại số",
                "cognitive_level_code": "KNOW",
                "question_count": 1,
                "target_score": 0.25,
            },
        ),
        specification=(
            {
                "requirement_code": "M6_REQ_001",
                "requirement_text": (
                    "Nhận biết được tập hợp số tự nhiên."
                ),
                "allocation_scope": "TOPIC",
                "topic_matrix_allocations": (
                    {
                        "cognitive_level_code": "KNOW",
                    },
                ),
            },
        ),
        questions=(
            {
                "display_number": 1,
                "prompt_text": (
                    "Số tự nhiên nhỏ nhất là số nào?"
                ),
            },
        ),
        answer_key=(
            {
                "display_number": 1,
                "correct_options": ("A",),
            },
        ),
        scoring_guide=(
            {
                "display_number": 1,
                "assigned_score": 0.25,
            },
        ),
    )


def _matrix_template() -> AssessmentTemplateDefinition:
    return AssessmentTemplateDefinition(
        document_type_code="MATRIX",
        renderer_code="DOCX_JSON_V1",
        layout_schema={
            "page_orientation": "LANDSCAPE",
            "paper_size": "A4",
        },
        style_schema={
            "font_family": "Times New Roman",
            "font_size": 12,
        },
        binding_schema={
            "exam_title": "metadata.exam.exam_title",
            "matrix_rows": "matrix",
        },
        section_schema=(
            {
                "section_code": "HEADER",
                "section_type": "FIELDS",
                "bindings": ("exam_title",),
            },
            {
                "section_code": "MATRIX_BODY",
                "section_type": "TABLE",
                "bindings": ("matrix_rows",),
                "columns": (
                    {
                        "column_code": "TOPIC",
                        "value_path": "topic_name",
                    },
                    {
                        "column_code": "LEVEL",
                        "value_path": (
                            "cognitive_level_code"
                        ),
                    },
                ),
            },
        ),
        template_asset_path=(
            "assessment-templates/matrix-v1.docx"
        ),
        template_asset_hash="a" * 64,
    )


def test_renders_dynamic_matrix_plan() -> None:
    plan = DynamicAssessmentDocumentRenderer().render(
        document=_document(),
        template=_matrix_template(),
    )

    assert plan.schema_version == 1
    assert plan.document_type_code == "MATRIX"
    assert plan.renderer_code == "DOCX_JSON_V1"
    assert plan.bindings["exam_title"] == (
        "Đề kiểm tra giữa học kỳ I"
    )
    assert plan.bindings["matrix_rows"][0][
        "topic_name"
    ] == "Số và Đại số"
    assert plan.sections[1]["section_type"] == "TABLE"
    assert plan.sections[1]["data"]["matrix_rows"][0][
        "question_count"
    ] == 1


@pytest.mark.parametrize(
    ("document_type", "root"),
    (
        ("MATRIX", "matrix"),
        ("SPECIFICATION", "specification"),
        ("STUDENT_EXAM", "questions"),
        ("ANSWER_KEY", "answer_key"),
        ("SCORING_GUIDE", "scoring_guide"),
    ),
)
def test_supports_every_assessment_document_type(
    document_type: str,
    root: str,
) -> None:
    template = AssessmentTemplateDefinition(
        document_type_code=document_type,
        renderer_code="DOCX_JSON_V1",
        layout_schema={},
        style_schema={},
        binding_schema={
            "rows": root,
        },
        section_schema=(
            {
                "section_code": "BODY",
                "section_type": "REPEAT",
                "bindings": ("rows",),
            },
        ),
    )

    plan = DynamicAssessmentDocumentRenderer().render(
        document=_document(),
        template=template,
    )

    assert plan.document_type_code == document_type
    assert len(plan.bindings["rows"]) == 1


def test_rejects_cross_document_protected_binding() -> None:
    template = AssessmentTemplateDefinition(
        document_type_code="STUDENT_EXAM",
        renderer_code="DOCX_JSON_V1",
        layout_schema={},
        style_schema={},
        binding_schema={
            "questions": "questions",
            "answers": "answer_key",
        },
        section_schema=(
            {
                "section_code": "BODY",
                "section_type": "REPEAT",
                "bindings": ("questions",),
            },
        ),
    )

    with pytest.raises(
        DynamicAssessmentRendererError,
        match="outside the permitted",
    ):
        DynamicAssessmentDocumentRenderer().render(
            document=_document(),
            template=template,
        )


def test_rejects_unknown_binding_path() -> None:
    template = AssessmentTemplateDefinition(
        document_type_code="MATRIX",
        renderer_code="DOCX_JSON_V1",
        layout_schema={},
        style_schema={},
        binding_schema={
            "missing": "metadata.exam.unknown_field",
        },
        section_schema=(
            {
                "section_code": "HEADER",
                "section_type": "FIELDS",
                "bindings": ("missing",),
            },
        ),
    )

    with pytest.raises(
        DynamicAssessmentRendererError,
        match="does not resolve",
    ):
        DynamicAssessmentDocumentRenderer().render(
            document=_document(),
            template=template,
        )


def test_rejects_section_unknown_binding() -> None:
    template = AssessmentTemplateDefinition(
        document_type_code="MATRIX",
        renderer_code="DOCX_JSON_V1",
        layout_schema={},
        style_schema={},
        binding_schema={
            "matrix_rows": "matrix",
        },
        section_schema=(
            {
                "section_code": "BODY",
                "section_type": "TABLE",
                "bindings": ("unknown",),
            },
        ),
    )

    with pytest.raises(
        DynamicAssessmentRendererError,
        match="unknown binding",
    ):
        DynamicAssessmentDocumentRenderer().render(
            document=_document(),
            template=template,
        )


def test_rejects_unsupported_renderer() -> None:
    with pytest.raises(
        DynamicAssessmentRendererError,
        match="unsupported renderer",
    ):
        AssessmentTemplateDefinition(
            document_type_code="MATRIX",
            renderer_code="ARBITRARY_PYTHON",
            layout_schema={},
            style_schema={},
            binding_schema={
                "rows": "matrix",
            },
            section_schema=(
                {
                    "section_code": "BODY",
                    "section_type": "TABLE",
                    "bindings": ("rows",),
                },
            ),
        )


def test_normalizes_binding_names() -> None:
    template = AssessmentTemplateDefinition(
        document_type_code="MATRIX",
        renderer_code="DOCX_JSON_V1",
        layout_schema={},
        style_schema={},
        binding_schema={
            " rows ": "matrix",
        },
        section_schema=(
            {
                "section_code": "BODY",
                "section_type": "TABLE",
                "bindings": ("rows",),
            },
        ),
    )

    plan = DynamicAssessmentDocumentRenderer().render(
        document=_document(),
        template=template,
    )

    assert "rows" in plan.bindings
    assert " rows " not in plan.bindings


def test_rejects_duplicate_normalized_binding_names() -> None:
    with pytest.raises(
        DynamicAssessmentRendererError,
        match="binding names must be unique",
    ):
        AssessmentTemplateDefinition(
            document_type_code="MATRIX",
            renderer_code="DOCX_JSON_V1",
            layout_schema={},
            style_schema={},
            binding_schema={
                "rows": "matrix",
                " rows ": "matrix",
            },
            section_schema=(
                {
                    "section_code": "BODY",
                    "section_type": "TABLE",
                    "bindings": ("rows",),
                },
            ),
        )


def test_rejects_duplicate_section_codes() -> None:
    with pytest.raises(
        DynamicAssessmentRendererError,
        match="section codes must be unique",
    ):
        AssessmentTemplateDefinition(
            document_type_code="MATRIX",
            renderer_code="DOCX_JSON_V1",
            layout_schema={},
            style_schema={},
            binding_schema={
                "rows": "matrix",
            },
            section_schema=(
                {
                    "section_code": "BODY",
                    "section_type": "TABLE",
                    "bindings": ("rows",),
                },
                {
                    "section_code": "BODY",
                    "section_type": "REPEAT",
                    "bindings": ("rows",),
                },
            ),
        )


@pytest.mark.parametrize(
    ("asset_path", "asset_hash", "message"),
    (
        (
            "templates/matrix.docx",
            None,
            "must be paired",
        ),
        (
            None,
            "a" * 64,
            "must be paired",
        ),
        (
            "templates/matrix.docx",
            "not-a-sha256",
            "must be SHA-256",
        ),
    ),
)
def test_rejects_invalid_template_asset_contract(
    asset_path: str | None,
    asset_hash: str | None,
    message: str,
) -> None:
    with pytest.raises(
        DynamicAssessmentRendererError,
        match=message,
    ):
        AssessmentTemplateDefinition(
            document_type_code="MATRIX",
            renderer_code="DOCX_JSON_V1",
            layout_schema={},
            style_schema={},
            binding_schema={
                "rows": "matrix",
            },
            section_schema=(
                {
                    "section_code": "BODY",
                    "section_type": "TABLE",
                    "bindings": ("rows",),
                },
            ),
            template_asset_path=asset_path,
            template_asset_hash=asset_hash,
        )


def test_plan_is_deeply_immutable() -> None:
    plan = DynamicAssessmentDocumentRenderer().render(
        document=_document(),
        template=_matrix_template(),
    )

    with pytest.raises(TypeError):
        plan.layout["paper_size"] = "A3"

    with pytest.raises(TypeError):
        plan.bindings["matrix_rows"][0][
            "topic_name"
        ] = "Changed"

    with pytest.raises(TypeError):
        plan.sections[1]["columns"][0][
            "column_code"
        ] = "Changed"

    with pytest.raises(FrozenInstanceError):
        plan.schema_version = 2


def test_template_change_requires_no_renderer_change() -> None:
    first = _matrix_template()

    second = AssessmentTemplateDefinition(
        document_type_code="MATRIX",
        renderer_code="DOCX_JSON_V1",
        layout_schema={
            "page_orientation": "PORTRAIT",
            "paper_size": "A3",
        },
        style_schema={
            "font_family": "Arial",
            "font_size": 11,
        },
        binding_schema={
            "title": "metadata.exam.exam_title",
            "rows": "matrix",
        },
        section_schema=(
            {
                "section_code": "AUTHORITY_HEADER",
                "section_type": "FIELDS",
                "bindings": ("title",),
            },
            {
                "section_code": "CUSTOM_MATRIX",
                "section_type": "TABLE",
                "bindings": ("rows",),
                "columns": (
                    {
                        "column_code": "CUSTOM_TOPIC",
                        "value_path": "topic_name",
                    },
                ),
            },
        ),
    )

    renderer = DynamicAssessmentDocumentRenderer()

    first_plan = renderer.render(
        document=_document(),
        template=first,
    )
    second_plan = renderer.render(
        document=_document(),
        template=second,
    )

    assert first_plan.layout["paper_size"] == "A4"
    assert second_plan.layout["paper_size"] == "A3"
    assert first_plan.styles["font_family"] == (
        "Times New Roman"
    )
    assert second_plan.styles["font_family"] == "Arial"
    assert first_plan.sections[1]["section_code"] == (
        "MATRIX_BODY"
    )
    assert second_plan.sections[1]["section_code"] == (
        "CUSTOM_MATRIX"
    )


def test_renderer_has_no_authority_specific_terms() -> None:
    from pathlib import Path

    source = Path(
        "src/assessment_generation_v2/renderers/"
        "dynamic_document_renderer.py"
    ).read_text(encoding="utf-8-sig")

    forbidden = (
        "DIEN_BIEN",
        "PHONG_GIAO_DUC",
        "SO_GIAO_DUC",
        "TRUONG_",
        "Mau_Phong",
        "Mau_So",
    )

    for value in forbidden:
        assert value not in source
