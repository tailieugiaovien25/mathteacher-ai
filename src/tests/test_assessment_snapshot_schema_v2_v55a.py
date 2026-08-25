from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608250019_assessment_snapshot_schema_v2.sql"
)


def _text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def test_schema_one_builder_is_preserved() -> None:
    text = _text()

    assert (
        "rename to "
        "build_assessment_exam_snapshot_document_v1"
    ) in text
    assert (
        "build_assessment_exam_snapshot_document_v1("
        in text
    )


def test_new_snapshot_builder_emits_schema_two() -> None:
    text = _text()

    assert "'{snapshot_schema_version}'" in text
    assert "'2'::jsonb" in text


def test_blueprint_snapshot_has_required_collections() -> None:
    text = _text()

    assert "'sections'" in text
    assert "'matrix_cells'" in text
    assert "'requirement_links'" in text


def test_sections_capture_rendering_labels_and_counts() -> None:
    text = _text()

    fields = (
        "'section_code'",
        "'section_name'",
        "'question_type_code'",
        "'question_type_name'",
        "'answer_mode'",
        "'question_count'",
        "'response_count'",
        "'section_score'",
        "'score_per_response'",
        "'instructions'",
    )

    for field in fields:
        assert field in text


def test_matrix_cells_capture_all_matrix_dimensions() -> None:
    text = _text()

    fields = (
        "'blueprint_cell_id'",
        "'topic_code'",
        "'topic_name'",
        "'domain_code'",
        "'cognitive_level_code'",
        "'cognitive_level_name'",
        "'question_type_code'",
        "'question_type_name'",
        "'question_count'",
        "'response_count'",
        "'target_score'",
        "'specification_note'",
    )

    for field in fields:
        assert field in text


def test_requirements_capture_historical_text() -> None:
    text = _text()

    fields = (
        "'requirement_code'",
        "'requirement_text'",
        "'requirement_version_number'",
        "'source_locator'",
        "'coverage_role'",
        "'target_question_count'",
        "'target_score'",
        "'specification_note'",
    )

    for field in fields:
        assert field in text


def test_requirements_capture_competency_labels() -> None:
    text = _text()

    assert (
        "assessment_requirement_competency_links"
        in text
    )
    assert (
        "assessment_mathematical_competencies"
        in text
    )
    assert "'competency_code'" in text
    assert "'competency_name'" in text
    assert "'description'" in text


def test_snapshot_uses_labels_not_only_codes() -> None:
    text = _text()

    required_labels = (
        "topic.topic_name",
        "profile_section.section_name",
        "cognitive_level.cognitive_level_name",
        "question_type.question_type_name",
        "requirement.requirement_text",
        "competency.competency_name",
    )

    for label in required_labels:
        assert label in text


def test_blueprint_arrays_have_deterministic_order() -> None:
    text = _text()

    assert "profile_section.sequence_number" in text
    assert "blueprint_cell.sequence_number" in text
    assert "topic.sequence_number" in text
    assert "cognitive_level.sequence_number" in text
    assert "requirement_link.sequence_number" in text
    assert "competency.sequence_number" in text


def test_snapshot_builder_does_not_depend_on_output_template() -> None:
    text = _text()

    forbidden = (
        "template_code",
        "template_version",
        "layout_schema",
        "style_schema",
        "DOCX",
        "PDF",
        "DIEN_BIEN",
    )

    for value in forbidden:
        assert value not in text


def test_public_cannot_execute_internal_snapshot_builders() -> None:
    text = _text()

    assert text.count(
        "revoke all on function"
    ) == 2
    assert "from public;" in text


def test_snapshot_v2_preserves_original_exam_questions() -> None:
    text = _text()

    assert (
        "base_snapshot.snapshot_document"
        in text
    )
    assert (
        "-> 'blueprint'"
        in text
    )
    assert "jsonb_set(" in text
