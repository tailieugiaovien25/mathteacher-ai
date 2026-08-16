from pathlib import Path


def _root() -> Path:
    return Path(
        __file__
    ).resolve().parents[3]


def _catalog_sql() -> str:
    return (
        _root()
        / "supabase"
        / "migrations"
        / "202608160005_subject_catalog.sql"
    ).read_text(
        encoding="utf-8"
    ).lower()


def _registration_sql() -> str:
    return (
        _root()
        / "supabase"
        / "migrations"
        / "202608160007_teacher_subject_registrations.sql"
    ).read_text(
        encoding="utf-8"
    ).lower()


def test_subject_components_expose_composite_identity():
    sql = _catalog_sql()

    assert (
        "subject_components_subject_component_unique"
        in sql
    )

    assert (
        "unique (\n"
        "            subject_id,\n"
        "            component_id\n"
        "        )"
        in sql
    )


def test_registration_uses_composite_subject_component_fk():
    sql = _registration_sql()

    assert (
        "teacher_subject_registration_component_scope_fk"
        in sql
    )

    assert (
        "foreign key (\n"
        "            subject_id,\n"
        "            component_id\n"
        "        )"
        in sql
    )

    assert (
        "references public.subject_components (\n"
        "            subject_id,\n"
        "            component_id\n"
        "        )"
        in sql
    )


def test_component_only_fk_is_not_used():
    sql = _registration_sql()

    assert (
        "references public.subject_components(\n"
        "                component_id\n"
        "            )"
        not in sql
    )


def test_subject_fk_is_still_preserved():
    sql = _registration_sql()

    assert (
        "references public.subjects"
        in sql
    )


def test_component_id_remains_nullable():
    sql = _registration_sql()

    assert "component_id text null" in sql


def test_registration_rls_is_preserved():
    sql = _registration_sql()

    assert (
        "enable row level security"
        in sql
    )

    assert "auth.uid()" in sql
    assert "owner_id" in sql
