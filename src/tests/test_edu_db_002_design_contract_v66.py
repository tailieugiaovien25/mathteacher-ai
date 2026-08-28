from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CONTRACT = (
    ROOT
    / "docs"
    / "educational_database"
    / "EDU_DB_002_CONTENT_SOURCE_TEXTBOOK_CATALOG.md"
)

SCHEMA = (
    ROOT
    / "docs"
    / "educational_database"
    / "EDU_DB_002_SCHEMA_CONTRACT.md"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_edu_db_002_contract_files_exist():
    assert CONTRACT.exists()
    assert SCHEMA.exists()


def test_data_changes_system_does_not():
    text = _read(CONTRACT)

    assert "Data may change; the system must not change." in text
    assert "hard-code textbook names" in text


def test_math_and_english_share_architecture():
    text = _read(CONTRACT)

    assert "subject-math" in text
    assert "subject-foreign-language-1" in text
    assert "same source architecture" in text


def test_english_is_first_class_subject():
    text = _read(CONTRACT)

    assert "English is a first-class subject." in text
    assert "are NOT subjects" in text
    assert "are NOT subject components" in text


def test_initial_textbook_families_are_data_targets():
    text = _read(CONTRACT)

    ket_noi = (
        "K\u1ebft n\u1ed1i tri th\u1ee9c "
        "v\u1edbi cu\u1ed9c s\u1ed1ng"
    )

    assert ket_noi in text
    assert "Global Success" in text


def test_shared_media_architecture_supports_english_assets():
    text = _read(CONTRACT)

    required = (
        "audio tracks",
        "listening scripts",
        "pronunciation audio",
        "video",
        "images",
        "transcripts",
        "supplementary worksheets",
    )

    for value in required:
        assert value in text


def test_admin_can_extend_without_code_changes():
    text = _read(CONTRACT)

    assert "ADMIN MUST be able to:" in text

    required_operations = (
        "add sources",
        "deactivate sources",
        "create new source versions",
        "add textbook editions",
        "edit metadata",
        "add grades",
        "add future subjects",
        "add media assets",
        "correct source mappings",
    )

    for operation in required_operations:
        assert operation in text

    assert (
        "Adding another subject does not require "
        "redesigning the schema."
    ) in text


def test_schema_reuses_edu_db_001():
    text = _read(SCHEMA)

    for table in (
        "education_programs",
        "grades",
        "education_program_scopes",
        "educational_sources",
        "educational_source_versions",
        "canonical_entity_links",
    ):
        assert table in text

    assert "MUST reuse these foundations" in text


def test_new_catalog_entities_are_declared():
    text = _read(SCHEMA)

    for entity in (
        "textbook_catalog",
        "textbook_units",
        "media_assets",
        "educational_asset_links",
    ):
        assert entity in text


def test_textbook_hierarchy_is_data_driven():
    text = _read(SCHEMA)

    assert "parent_unit_id" in text
    assert "arbitrary hierarchy" in text


def test_storage_is_provider_independent():
    text = _read(SCHEMA)

    assert "storage_provider" in text
    assert "storage_locator" in text
    assert "Storage credentials MUST NEVER" in text


def test_migration_contract_is_additive():
    text = _read(SCHEMA)

    assert "MUST be additive" in text

    for forbidden_goal in (
        "drop current tables",
        "delete existing operational data",
        "rename current application tables",
        "replace stable subject identities",
    ):
        assert forbidden_goal in text
