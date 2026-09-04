from lesson_planning_v2.services.lesson_plan_smart_up_resolver import (
    SmartUpContext,
    SmartUpDocument,
    resolve_documents,
)


def ctx(name="KHBD.ANH6.TUAN03.docx"):
    return SmartUpContext(
        expected_file_name=name,
        subject_ref="ANH",
        component_ref="",
        grade="6",
        week_number=3,
        lesson_id="",
        lesson_title="Unit 1: My new school - Looking back + Project",
        curriculum_periods=(1, 2, 3),
        aliases=(),
    )


def doc(name, *, title="", tags=()):
    return SmartUpDocument(
        file_name=name,
        storage_provider="google_drive_oauth",
        storage_file_id=name,
        title=title,
        description="",
        tags=tags,
    )


def test_exact_canonical_filename_wins_over_old_unit_files():
    resolution = resolve_documents(
        (
            doc("Unit9_NLS+HSKT.docx", title="English 6 week 3"),
            doc("Unit8_NLS_HSKT.docx", title="English 6 week 3"),
            doc("KHBD.ANH6.TUAN03.docx"),
        ),
        ctx(),
    )
    assert resolution.status == "FOUND"
    assert resolution.best.document.file_name == "KHBD.ANH6.TUAN03.docx"
    assert resolution.best.match_reason == "EXACT_CANONICAL_FILENAME"


def test_week_number_padding_is_harmless_normalization():
    resolution = resolve_documents(
        (doc("KHBD.ANH6.TUAN3.docx"),),
        ctx(),
    )
    assert resolution.status == "FOUND"
    assert resolution.best.document.file_name == "KHBD.ANH6.TUAN3.docx"
    assert resolution.best.match_reason == "NORMALIZED_CANONICAL_FILENAME"


def test_separator_variation_is_harmless_normalization():
    resolution = resolve_documents(
        (doc("KHBD-ANH6-TUAN3.docx"),),
        ctx(),
    )
    assert resolution.status == "FOUND"
    assert resolution.best.document.file_name == "KHBD-ANH6-TUAN3.docx"
    assert resolution.best.match_reason == "NORMALIZED_CANONICAL_FILENAME"


def test_unrelated_unit_files_do_not_beat_group_filename():
    resolution = resolve_documents(
        (
            doc("Unit9_NLS+HSKT.docx", title="ANH 6 TUAN 3"),
            doc("Unit7_NLS_HSKT.docx", title="ANH 6 TUAN 3"),
            doc("KHBD-ANH6-TUAN3.docx"),
        ),
        ctx(),
    )
    assert resolution.status == "FOUND"
    assert resolution.best.document.file_name == "KHBD-ANH6-TUAN3.docx"
    assert resolution.best.match_reason == "NORMALIZED_CANONICAL_FILENAME"