from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]

SCHEMA = (
    ROOT
    / "docs"
    / "educational_database"
    / "EDU_DB_002_SCHEMA_CONTRACT.md"
)

PHYSICAL = (
    ROOT
    / "docs"
    / "educational_database"
    / "EDU_DB_002_PHYSICAL_SCHEMA_CONTRACT.md"
)

FOUNDATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608260002_educational_core_identity_foundation.sql"
)


def _read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig"
    )


def test_contract_uses_repository_metadata_name():
    schema = _read(SCHEMA)
    physical = _read(PHYSICAL)

    # The logical and physical contracts may document fields
    # using different Markdown structures. Test semantics,
    # not presentation formatting.
    assert "metadata" in schema
    assert "metadata" in physical

    forbidden_physical_declarations = (
        "metadata_json jsonb",
        "metadata_json | jsonb",
        "`metadata_json` | `jsonb`",
    )

    for value in forbidden_physical_declarations:
        assert value not in schema
        assert value not in physical

    assert re.search(
        r"metadata_json\s+as\s+a\s+competing\s+"
        r"column\s+convention",
        physical,
        flags=re.IGNORECASE,
    )


def test_repository_uses_metadata_jsonb():
    foundation = _read(FOUNDATION)

    assert "metadata jsonb not null" in foundation
    assert "metadata_json jsonb" not in foundation


def test_canonical_identity_types_are_text():
    foundation = _read(FOUNDATION)

    required = (
        "program_id text primary key",
        "grade_id text primary key",
        "source_id text primary key",
        "source_version_id text primary key",
    )

    for value in required:
        assert value in foundation


def test_subject_identity_is_text():
    subject_migration = (
        ROOT
        / "supabase"
        / "migrations"
        / "202608160005_subject_catalog.sql"
    )

    text = _read(subject_migration)

    assert "subject_id text primary key" in text


def test_program_scope_foreign_keys_restrict_delete():
    foundation = _read(FOUNDATION)

    assert (
        "references public.education_programs("
        in foundation
    )
    assert (
        "references public.subjects("
        in foundation
    )
    assert (
        "references public.grades("
        in foundation
    )

    scope_start = foundation.index(
        "public.education_program_scopes"
    )

    scope_end = foundation.index(
        "public.educational_sources",
        scope_start,
    )

    scope = foundation[
        scope_start:scope_end
    ]

    assert scope.count(
        "on delete restrict"
    ) >= 3


def test_educational_source_version_contract_is_known():
    foundation = _read(FOUNDATION)

    assert "source_version_id text primary key" in foundation
    assert "version_number integer not null" in foundation
    assert "checksum_sha256 text" in foundation
    assert "verification_status text not null" in foundation
    assert "publication_status text not null" in foundation


def test_alignment_contract_uses_catalog_governance():
    text = _read(PHYSICAL)

    assert (
        "anon receives no direct table privileges"
        in text
    )

    assert (
        "authenticated users may receive SELECT access"
        in text
    )

    assert (
        "direct authenticated INSERT/UPDATE/DELETE "
        "is not granted by default"
        in text
    )

    assert (
        "governed ADMIN/service operations perform mutations"
        in text
    )


def test_new_tables_keep_mutable_catalog_timestamps():
    text = _read(PHYSICAL)

    assert (
        "New EDU-DB-002 tables contain created_at and updated_at"
        in text
    )

    assert (
        "does not imply that every pre-existing EDU-DB-001 table"
        in text
    )


def test_index_convention_is_locked():
    text = _read(PHYSICAL)

    assert "create index if not exists" in text


def test_repository_alignment_section_exists():
    text = _read(PHYSICAL)

    assert "# 14. Repository alignment rules" in text
