from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608250002_assessment_curriculum_foundation.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def test_assessment_curriculum_foundation_migration_exists() -> None:
    assert MIGRATION.exists()


def test_assessment_foundation_defines_required_tables() -> None:
    text = _migration_text()

    required_tables = (
        "assessment_curriculum_programs",
        "assessment_curriculum_topics",
        "assessment_learning_requirements",
        "assessment_mathematical_competencies",
        "assessment_requirement_competency_links",
        "assessment_regulatory_documents",
    )

    for table_name in required_tables:
        assert f"create table if not exists public.{table_name}" in text


def test_assessment_foundation_uses_versioned_canonical_requirements() -> None:
    text = _migration_text()

    assert "requirement_code text primary key" in text
    assert "version_number integer not null default 1" in text
    assert "replaces_requirement_code text null" in text
    assert "source_locator text null" in text
    assert "book_independent" in text


def test_assessment_foundation_enables_rls_for_every_table() -> None:
    text = _migration_text()

    required_tables = (
        "assessment_curriculum_programs",
        "assessment_curriculum_topics",
        "assessment_learning_requirements",
        "assessment_mathematical_competencies",
        "assessment_requirement_competency_links",
        "assessment_regulatory_documents",
    )

    for table_name in required_tables:
        assert (
            f"alter table public.{table_name}\n"
            "    enable row level security;"
        ) in text

    assert "current_user_is_portal_admin()" in text
    assert "to authenticated" in text
    assert "from anon" in text


def test_assessment_foundation_seeds_math_program_and_competencies() -> None:
    text = _migration_text()

    assert "MOET-GDPT2018-MATH-THCS" in text
    assert "'M6-SH'" in text
    assert "'M6-HH'" in text
    assert "'M6-TKXS'" in text

    competency_codes = (
        "MATH-REASONING",
        "MATH-MODELING",
        "MATH-PROBLEM-SOLVING",
        "MATH-COMMUNICATION",
        "MATH-TOOLS",
    )

    for competency_code in competency_codes:
        assert competency_code in text


def test_assessment_foundation_records_regulatory_scope_safely() -> None:
    text = _migration_text()

    assert "TT-32-2018-BGDDT" in text
    assert "TT-22-2021-BGDDT" in text
    assert "TT-17-2025-BGDDT" in text
    assert "CV-7991-2024-BGDDT-GDTRH" in text
    assert "do_not_assume_mandatory_for_thcs" in text
    assert "requires_local_guidance" in text


def test_assessment_foundation_does_not_hard_code_exam_profile() -> None:
    text = _migration_text()

    assert "MATH-THCS-DEFAULT-3223-V1" not in text
    assert "assessment_profiles" not in text
    assert "assessment_profile_sections" not in text
