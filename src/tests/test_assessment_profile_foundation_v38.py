from decimal import Decimal
from pathlib import Path
import re


MIGRATION = Path(
    "supabase/migrations/"
    "202608250003_assessment_profile_foundation.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def test_assessment_profile_foundation_migration_exists() -> None:
    assert MIGRATION.exists()


def test_assessment_profile_foundation_defines_seven_tables() -> None:
    text = _migration_text()

    required_tables = (
        "assessment_types",
        "assessment_question_types",
        "assessment_cognitive_levels",
        "assessment_profiles",
        "assessment_profile_sections",
        "assessment_profile_level_allocations",
        "assessment_profile_regulatory_links",
    )

    for table_name in required_tables:
        assert (
            f"create table if not exists public.{table_name}"
            in text
        )


def test_assessment_profile_is_versioned_and_not_hard_coded() -> None:
    text = _migration_text()

    assert "version_number integer not null default 1" in text
    assert "replaces_profile_code text null" in text
    assert "effective_from date null" in text
    assert "effective_to date null" in text
    assert "no exam structure is hard-coded" in text


def test_profile_sections_distinguish_questions_and_responses() -> None:
    text = _migration_text()

    assert "question_count integer not null" in text
    assert "response_count integer not null" in text
    assert "check (response_count >= question_count)" in text

    true_false_section = re.search(
        r"'TF',.*?'TRUE_FALSE',.*?20,.*?2,.*?8,"
        r".*?2\.00,.*?0\.25",
        text,
        flags=re.DOTALL,
    )
    assert true_false_section is not None


def test_default_profile_scores_sum_to_ten() -> None:
    scores = (
        Decimal("3.00"),
        Decimal("2.00"),
        Decimal("2.00"),
        Decimal("3.00"),
    )

    assert sum(scores) == Decimal("10.00")


def test_default_profile_levels_sum_to_one_hundred_percent() -> None:
    percentages = (
        Decimal("40.00"),
        Decimal("30.00"),
        Decimal("30.00"),
    )

    assert sum(percentages) == Decimal("100.00")


def test_thcs_reference_profile_requires_local_approval() -> None:
    text = _migration_text()

    assert "MATH-THCS-DEFAULT-3223-V1" in text
    assert "'DRAFT'" in text
    assert "'requires_local_approval', true" in text
    assert "'not_nationally_mandatory_for_thcs', true" in text
    assert "'REFERENCE'" in text


def test_assessment_profile_foundation_enables_rls() -> None:
    text = _migration_text()

    required_tables = (
        "assessment_types",
        "assessment_question_types",
        "assessment_cognitive_levels",
        "assessment_profiles",
        "assessment_profile_sections",
        "assessment_profile_level_allocations",
        "assessment_profile_regulatory_links",
    )

    for table_name in required_tables:
        assert (
            f"alter table public.{table_name}\n"
            "    enable row level security;"
        ) in text

    assert "current_user_is_portal_admin()" in text
    assert "from anon" in text
    assert "to authenticated" in text


def test_profile_links_regulatory_authority_and_reference() -> None:
    text = _migration_text()

    assert "TT-22-2021-BGDDT" in text
    assert "TT-32-2018-BGDDT" in text
    assert "CV-7991-2024-BGDDT-GDTRH" in text
    assert "Ch\u1ec9 s\u1eed d\u1ee5ng l\u00e0m m\u1eabu k\u1ef9 thu\u1eadt" in text
