from lesson_planning_v2.services.lesson_plan_smart_up_resolver import (
    SmartUpContext,
    SmartUpDocument,
    resolve_documents,
)


def _doc(name, file_id, *, title="", tags=()):
    return SmartUpDocument(
        file_name=name,
        storage_provider="google_drive_oauth",
        storage_file_id=file_id,
        title=title,
        tags=tags,
    )


def test_exact_canonical_filename_wins_without_business_id_coupling():
    context = SmartUpContext(
        expected_file_name="KHBD.TDS6.TUAN01.docx",
        subject_ref="TOAN",
        component_ref="TDS",
        grade="6",
        week_number=1,
    )
    result = resolve_documents(
        (
            _doc("6GTDS001.docx", "legacy-id", tags=("TDS", "6", "TUAN01")),
            _doc("KHBD.TDS6.TUAN01.docx", "canonical-id"),
        ),
        context,
    )
    assert result.status == "FOUND"
    assert result.best.document.storage_file_id == "canonical-id"
    assert result.best.match_reason == "EXACT_CANONICAL_FILENAME"


def test_known_alias_is_accepted_below_exact_canonical_name():
    context = SmartUpContext(
        expected_file_name="KHBD.TDS6.TUAN01.docx",
        aliases=("6GTDS001.docx",),
    )
    result = resolve_documents((_doc("6GTDS001.docx", "old"),), context)
    assert result.status == "FOUND"
    assert result.best.score == 900
    assert result.best.match_reason == "KNOWN_ALIAS_FILENAME"


def test_context_metadata_is_safe_fallback():
    context = SmartUpContext(
        expected_file_name="KHBD.TDS6.TUAN01.docx",
        component_ref="TDS",
        grade="6",
        week_number=1,
        lesson_title="Phan so",
    )
    result = resolve_documents(
        (_doc("giao-an-cu.docx", "ctx", title="Phan so", tags=("TDS", "6", "TUAN01")),),
        context,
    )
    assert result.status == "FOUND"
    assert result.best.match_reason.startswith("CONTEXT_METADATA:")


def test_multiple_equal_exact_matches_are_not_silently_chosen():
    context = SmartUpContext(expected_file_name="KHBD.TDS6.TUAN01.docx")
    result = resolve_documents(
        (
            _doc("KHBD.TDS6.TUAN01.docx", "drive-a"),
            _doc("KHBD.TDS6.TUAN01.docx", "drive-b"),
        ),
        context,
    )
    assert result.status == "MULTIPLE"
    assert len(result.candidates) == 2


def test_not_found_when_no_filename_alias_or_context_match():
    context = SmartUpContext(
        expected_file_name="KHBD.TDS6.TUAN01.docx",
        component_ref="TDS",
        grade="6",
        week_number=1,
    )
    result = resolve_documents((_doc("KHBD.ANH9.TUAN20.docx", "wrong"),), context)
    assert result.status == "NOT_FOUND"
    assert result.best is None