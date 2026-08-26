from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CONTRACT = (
    ROOT
    / "docs"
    / "educational_database"
    / "EDU_DB_002_PHYSICAL_SCHEMA_CONTRACT.md"
)


def _read() -> str:
    return CONTRACT.read_text(encoding="utf-8-sig")


def test_physical_contract_exists():
    assert CONTRACT.exists()


def test_reuses_edu_db_001_foundation():
    text = _read()

    required = (
        "public.education_programs",
        "public.grades",
        "public.education_program_scopes",
        "public.educational_sources",
        "public.educational_source_versions",
        "public.canonical_entity_links",
        "public.subjects",
    )

    for value in required:
        assert value in text

    assert "MUST NOT be duplicated" in text


def test_exactly_four_new_logical_tables_declared():
    text = _read()

    for value in (
        "public.textbook_catalog",
        "public.textbook_units",
        "public.media_assets",
        "public.educational_asset_links",
    ):
        assert value in text

    assert (
        "four new physical tables"
        in text.lower()
    )


def test_textbook_catalog_foreign_keys_declared():
    text = _read()

    required = (
        "public.educational_sources(source_id)",
        "public.education_programs(program_id)",
        "public.subjects(subject_id)",
        "public.grades(grade_id)",
    )

    for value in required:
        assert value in text


def test_textbook_unique_scope_declared():
    text = _read()

    assert (
        "(program_id, subject_id, grade_id, textbook_code)"
        in text
    )


def test_textbook_units_support_hierarchy():
    text = _read()

    assert "parent_unit_id" in text
    assert "self FOREIGN KEY" in text
    assert "Cross-textbook parenting MUST also be prevented." in text
    assert "parent_unit_id = textbook_unit_id" in text


def test_media_types_cover_rich_english_content():
    text = _read()

    for value in (
        "PDF",
        "IMAGE",
        "AUDIO",
        "VIDEO",
        "TRANSCRIPT",
        "DOCUMENT",
        "WORKSHEET",
        "ARCHIVE",
        "EXTERNAL_LINK",
    ):
        assert value in text


def test_media_storage_is_provider_independent():
    text = _read()

    for value in (
        "SUPABASE",
        "GOOGLE_DRIVE",
        "LOCAL_IMPORT",
        "EXTERNAL",
        "storage_locator",
        "external_url",
    ):
        assert value in text

    assert "MUST NOT contain passwords" in text


def test_media_requires_locator_or_url():
    text = _read()

    assert "At least one must be present:" in text
    assert "storage_locator" in text
    assert "external_url" in text


def test_asset_link_uniqueness_declared():
    text = _read()

    assert (
        "(media_asset_id, entity_type, entity_id, relation_type)"
        in text
    )


def test_english_remains_first_class_subject():
    text = _read()

    assert (
        "subject_id = subject-foreign-language-1"
        in text
    )

    assert (
        "MUST NOT create subject components"
        in text
    )


def test_math_and_english_share_media_architecture():
    text = _read()

    assert "subject_id = subject-math" in text
    assert "media_assets + educational_asset_links" in text
    assert "same media_assets and educational_asset_links tables" in text


def test_initial_scope_contains_grades_6_to_9():
    text = _read()

    for grade_id in (
        "grade-06",
        "grade-07",
        "grade-08",
        "grade-09",
    ):
        assert grade_id in text

    assert "program-vn-gdpt-2018" in text


def test_initial_textbook_families_are_present():
    text = _read()

    ket_noi = (
        "K\u1ebft n\u1ed1i tri th\u1ee9c "
        "v\u1edbi cu\u1ed9c s\u1ed1ng"
    )

    assert ket_noi in text
    assert "Global Success" in text


def test_migration_remains_additive():
    text = _read()

    assert "be additive" in text

    forbidden_operations = (
        "DROP existing application tables",
        "DELETE existing operational records",
        "TRUNCATE existing tables",
    )

    for value in forbidden_operations:
        assert value in text


def test_existing_foundations_must_not_be_duplicated():
    text = _read()

    for value in (
        "duplicate education_programs",
        "duplicate grades",
        "duplicate subjects",
        "duplicate educational_sources",
        "duplicate educational_source_versions",
    ):
        assert value in text


def test_status_lifecycle_is_explicit():
    text = _read()

    for value in (
        "DRAFT",
        "ACTIVE",
        "INACTIVE",
        "ARCHIVED",
        "BROKEN",
    ):
        assert value in text


def test_indexes_are_explicit():
    text = _read()

    assert "Required indexes:" in text
    assert "(entity_type, entity_id)" in text
    assert "(textbook_id, parent_unit_id, display_order)" in text


def test_rls_and_privilege_contract_exists():
    text = _read()

    assert "RLS and privileges" in text
    assert (
        "MUST NOT casually grant broad public write access"
        in text
    )
    assert (
        "ADMIN write capability will be exposed through "
        "governed application"
        in text
    )
    assert (
        "services, not direct anonymous table writes."
        in text
    )
