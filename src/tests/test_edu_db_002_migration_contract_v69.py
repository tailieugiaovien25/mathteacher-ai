from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]

MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608260003_educational_content_textbook_catalog.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def test_migration_exists():
    assert MIGRATION.exists()


def test_exact_four_new_tables():
    sql = _sql()

    tables = re.findall(
        r"create\s+table\s+if\s+not\s+exists\s+"
        r"public\.([a-z0-9_]+)",
        sql,
        flags=re.IGNORECASE,
    )

    assert tables == [
        "textbook_catalog",
        "textbook_units",
        "media_assets",
        "educational_asset_links",
    ]


def test_reuses_edu_db_001_foundation():
    sql = _sql()

    required = (
        "public.educational_sources",
        "public.educational_source_versions",
        "public.education_programs",
        "public.subjects",
        "public.grades",
    )

    for value in required:
        assert value in sql


def test_textbook_catalog_scope_foreign_keys():
    sql = _sql()

    required = (
        "references public.educational_sources(",
        "references public.education_programs(",
        "references public.subjects(",
        "references public.grades(",
    )

    for value in required:
        assert value in sql

    assert sql.count(
        "on delete restrict"
    ) >= 4


def test_textbook_catalog_unique_scope_code():
    sql = _sql()

    assert (
        "textbook_catalog_scope_code_unique"
        in sql
    )

    assert re.search(
        r"unique\s*\(\s*"
        r"program_id\s*,\s*"
        r"subject_id\s*,\s*"
        r"grade_id\s*,\s*"
        r"textbook_code\s*"
        r"\)",
        sql,
        flags=re.IGNORECASE,
    )


def test_textbook_units_same_textbook_parent_fk():
    sql = _sql()

    assert (
        "textbook_units_parent_same_textbook_fk"
        in sql
    )

    assert re.search(
        r"foreign\s+key\s*\(\s*"
        r"textbook_id\s*,\s*"
        r"parent_unit_id\s*"
        r"\)",
        sql,
        flags=re.IGNORECASE,
    )

    assert re.search(
        r"references\s+public\.textbook_units\s*"
        r"\(\s*textbook_id\s*,\s*"
        r"textbook_unit_id\s*\)",
        sql,
        flags=re.IGNORECASE,
    )


def test_textbook_unit_cannot_parent_itself():
    sql = _sql()

    assert (
        "textbook_units_parent_not_self_check"
        in sql
    )

    assert (
        "parent_unit_id <> textbook_unit_id"
        in sql
    )


def test_curriculum_period_range_guard():
    sql = _sql()

    assert (
        "textbook_units_curriculum_period_check"
        in sql
    )

    assert (
        "curriculum_period_to"
        in sql
    )

    assert (
        "curriculum_period_from"
        in sql
    )


def test_media_source_version_uses_set_null():
    sql = _sql()

    pattern = re.compile(
        r"source_version_id\s+text"
        r".*?"
        r"references\s+"
        r"public\.educational_source_versions"
        r".*?"
        r"on\s+delete\s+set\s+null",
        flags=re.IGNORECASE | re.DOTALL,
    )

    assert pattern.search(sql)


def test_media_types_are_shared_and_complete():
    sql = _sql()

    required = (
        "'PDF'",
        "'IMAGE'",
        "'AUDIO'",
        "'VIDEO'",
        "'TRANSCRIPT'",
        "'DOCUMENT'",
        "'WORKSHEET'",
        "'ARCHIVE'",
        "'EXTERNAL_LINK'",
    )

    for value in required:
        assert value in sql


def test_storage_provider_contract():
    sql = _sql()

    for value in (
        "'SUPABASE'",
        "'GOOGLE_DRIVE'",
        "'LOCAL_IMPORT'",
        "'EXTERNAL'",
    ):
        assert value in sql


def test_asset_requires_locator_or_url():
    sql = _sql()

    assert (
        "media_assets_locator_check"
        in sql
    )

    assert "storage_locator" in sql
    assert "external_url" in sql


def test_checksum_sha256_guard():
    sql = _sql()

    assert (
        "^[A-Fa-f0-9]{64}$"
        in sql
    )


def test_asset_link_is_polymorphic():
    sql = _sql()

    for value in (
        "'TEXTBOOK'",
        "'TEXTBOOK_UNIT'",
        "'SOURCE'",
        "'SOURCE_VERSION'",
        "'PROGRAM_SCOPE'",
        "'CANONICAL_ENTITY'",
    ):
        assert value in sql


def test_asset_link_semantic_uniqueness():
    sql = _sql()

    assert (
        "educational_asset_links_semantic_unique"
        in sql
    )

    assert re.search(
        r"unique\s*\(\s*"
        r"media_asset_id\s*,\s*"
        r"entity_type\s*,\s*"
        r"entity_id\s*,\s*"
        r"relation_type\s*"
        r"\)",
        sql,
        flags=re.IGNORECASE,
    )


def test_metadata_column_uses_repository_convention():
    sql = _sql()

    assert len(
        re.findall(
            r"\bmetadata\s+jsonb\s+not\s+null",
            sql,
            flags=re.IGNORECASE,
        )
    ) == 4

    assert not re.search(
        r"\bmetadata_json\s+jsonb\b",
        sql,
        flags=re.IGNORECASE,
    )


def test_all_new_tables_have_timestamps():
    sql = _sql()

    assert sql.count(
        "created_at timestamptz"
    ) == 4

    assert sql.count(
        "updated_at timestamptz"
    ) == 4


def test_updated_at_trigger_function_exists():
    sql = _sql()

    assert (
        "public.set_educational_catalog_updated_at()"
        in sql
    )

    assert sql.count(
        "set_educational_catalog_updated_at"
    ) >= 5


def test_all_four_tables_enable_rls():
    sql = _sql()

    for table in (
        "textbook_catalog",
        "textbook_units",
        "media_assets",
        "educational_asset_links",
    ):
        assert (
            f"alter table public.{table}"
            in sql
        )

    assert sql.count(
        "enable row level security"
    ) == 4


def test_anon_and_authenticated_are_revoked_before_grants():
    sql = _sql()

    assert sql.count(
        "from anon, authenticated"
    ) == 4

    assert sql.count(
        "grant select"
    ) == 4


def test_authenticated_only_receives_select():
    sql = _sql().lower()

    assert "grant insert" not in sql
    assert "grant update" not in sql
    assert "grant delete" not in sql

    assert sql.count(
        "to authenticated"
    ) >= 8


def test_four_authenticated_read_policies():
    sql = _sql()

    assert sql.count(
        "create policy"
    ) == 4

    for policy in (
        "authenticated_read_textbook_catalog",
        "authenticated_read_textbook_units",
        "authenticated_read_media_assets",
        "authenticated_read_educational_asset_links",
    ):
        assert policy in sql


def test_indexes_use_repository_convention():
    sql = _sql()

    indexes = re.findall(
        r"create\s+index\s+if\s+not\s+exists",
        sql,
        flags=re.IGNORECASE,
    )

    assert len(indexes) >= 20


def test_migration_is_additive():
    sql = _sql().lower()

    forbidden = (
        "drop table",
        "truncate table",
        "delete from public.",
        "alter table public.subjects rename",
        "alter table public.education_programs rename",
        "alter table public.grades rename",
    )

    for value in forbidden:
        assert value not in sql


def test_does_not_duplicate_foundation_tables():
    sql = _sql().lower()

    forbidden_create = (
        "create table if not exists public.education_programs",
        "create table if not exists public.grades",
        "create table if not exists public.subjects",
        "create table if not exists public.educational_sources",
        "create table if not exists public.educational_source_versions",
    )

    for value in forbidden_create:
        assert value not in sql


def test_no_seed_dml_in_structure_migration():
    sql = _sql().lower()

    assert "insert into" not in sql
    assert "update public." not in sql
    assert "delete from" not in sql


def test_no_subject_specific_physical_table():
    sql = _sql().lower()

    forbidden = (
        "english_",
        "math_",
        "tieng_anh",
        "toan_",
    )

    create_table_lines = "\n".join(
        line
        for line in sql.splitlines()
        if "create table" in line
    )

    for value in forbidden:
        assert value not in create_table_lines
