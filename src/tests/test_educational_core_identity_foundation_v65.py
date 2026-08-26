from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]

MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608260002_educational_core_identity_foundation.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(
        encoding="utf-8"
    )


def test_migration_creates_six_foundation_tables():
    sql = _sql()

    tables = (
        "education_programs",
        "grades",
        "education_program_scopes",
        "educational_sources",
        "educational_source_versions",
        "canonical_entity_links",
    )

    for table in tables:
        pattern = (
            r"create\s+table\s+if\s+not\s+exists\s+"
            rf"public\.{re.escape(table)}\b"
        )
        assert re.search(
            pattern,
            sql,
            flags=re.IGNORECASE,
        )



def test_reuses_existing_subject_catalog():
    sql = _sql()

    assert (
        "create table if not exists "
        "public.subjects"
        not in sql
    )

    assert (
        "references public.subjects("
        in sql
    )


def test_english_is_first_class_subject():
    sql = _sql()

    assert (
        "subject-foreign-language-1"
        in sql
    )

    assert (
        "name = 'Tiếng Anh'"
        in sql
    )

    assert (
        "component_policy = 'NONE'"
        in sql
    )

    assert "subject-english" not in sql

    assert (
        "insert into public.subject_components"
        not in sql
    )

def test_language_skills_are_not_components():
    sql = _sql().lower()

    skills = (
        "listening",
        "speaking",
        "reading",
        "writing",
        "grammar",
        "vocabulary",
        "pronunciation",
    )

    for skill in skills:
        assert (
            f"component-{skill}"
            not in sql
        )


def test_program_scopes_use_existing_subject_ids():
    sql = _sql()

    assert "'subject-math'" in sql

    assert (
        "'subject-foreign-language-1'"
        in sql
    )

    assert (
        "generate_series(6, 9)"
        in sql
    )


def test_grades_support_1_to_12():
    sql = _sql()

    assert (
        "grade_number between 1 and 12"
        in sql
    )

    assert (
        "generate_series(1, 12)"
        in sql
    )

    assert "'PRIMARY'" in sql
    assert "'LOWER_SECONDARY'" in sql
    assert "'UPPER_SECONDARY'" in sql


def test_program_subject_grade_scope_unique():
    sql = _sql()

    assert (
        "unique ("
        in sql
    )

    assert (
        "program_id,"
        in sql
    )

    assert (
        "subject_id,"
        in sql
    )

    assert (
        "grade_id"
        in sql
    )


def test_source_versions_are_versioned():
    sql = _sql()

    assert (
        "version_number > 0"
        in sql
    )

    assert (
        "source_id,"
        in sql
    )

    assert (
        "version_number"
        in sql
    )

    assert "checksum_sha256" in sql
    assert "{64}" in sql


def test_sources_are_rights_aware():
    sql = _sql()

    tokens = (
        "rights_status",
        "VERIFIED_ALLOWED",
        "RESTRICTED",
        "INTERNAL_REFERENCE",
        "access_scope",
        "SYSTEM_INTERNAL",
        "AUTHORIZED_USERS",
        "PUBLIC",
    )

    for token in tokens:
        assert token in sql


def test_bridge_is_compatibility_only():
    sql = _sql()

    assert "canonical_entity_links" in sql

    assert "COMPATIBILITY" in sql
    assert "MIGRATION" in sql
    assert "TRACEABILITY" in sql

    assert (
        "references public.assessment_"
        not in sql
    )


def test_all_foundation_tables_enable_rls():
    sql = _sql()

    tables = (
        "education_programs",
        "grades",
        "education_program_scopes",
        "educational_sources",
        "educational_source_versions",
        "canonical_entity_links",
    )

    for table in tables:
        assert (
            f"public.{table}"
            in sql
        )

    assert (
        sql.count(
            "enable row level security"
        )
        >= 6
    )


def test_all_foundation_tables_revoke_anon():
    sql = _sql()

    tables = (
        "education_programs",
        "grades",
        "education_program_scopes",
        "educational_sources",
        "educational_source_versions",
        "canonical_entity_links",
    )

    for table in tables:
        assert (
            f"on table public.{table}"
            in sql
        )

    assert (
        sql.count("from anon")
        >= 6
    )


def test_admin_uses_portal_admin_helper():
    sql = _sql()

    assert (
        sql.count(
            "public.current_user_is_portal_admin()"
        )
        >= 6
    )

    assert "pr.role = 'ADMIN'" not in sql


def test_migration_is_additive_for_assessment():
    sql = _sql().lower()

    assert "drop table" not in sql

    assert (
        "alter table public.assessment_"
        not in sql
    )

    assert (
        "delete from public.assessment_"
        not in sql
    )


def test_only_foundation_reference_data_seeded():
    sql = _sql()

    assert (
        "program-vn-gdpt-2018"
        in sql
    )

    assert "VN_GDPT_2018" in sql

    assert "Global Success" not in sql

    assert "Kết nối tri thức" not in sql

def test_source_is_not_binary_asset():
    sql = _sql().lower()

    assert "bytea" not in sql
    assert "binary_data" not in sql
    assert "asset_blob" not in sql


def test_verified_source_version_requires_actor():
    sql = _sql()

    assert (
        "verification_status <> 'VERIFIED'"
        in sql
    )

    assert (
        "verified_at is not null"
        in sql
    )

    assert (
        "verified_by is not null"
        in sql
    )
