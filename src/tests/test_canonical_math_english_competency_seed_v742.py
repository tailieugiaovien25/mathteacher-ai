from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/202608270007_canonical_math_english_competency_seed.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_v742_seeds_exact_subject_component_backbone() -> None:
    sql = _sql()
    math_codes = (
        "NL-MATH-REASONING",
        "NL-MATH-MODELING",
        "NL-MATH-PROBLEM-SOLVING",
        "NL-MATH-COMMUNICATION",
        "NL-MATH-TOOLS",
    )
    english_codes = (
        "NL-ENG-LISTENING",
        "NL-ENG-SPEAKING",
        "NL-ENG-READING",
        "NL-ENG-WRITING",
        "NL-ENG-LANGUAGE-KNOWLEDGE",
    )
    for code in math_codes + english_codes:
        assert f"'{code}'" in sql
    assert "'competency-math'" in sql
    assert "'competency-english'" in sql


def test_v742_has_grade_band_indicators_and_evidence_policy() -> None:
    sql = _sql()
    assert sql.count("'review-required'") == 0
    assert sql.count('"mapping_policy":"review-required"') == 10
    assert sql.count(",6,9,'UNSPECIFIED'") == 10
    assert "evidence_guidance" in sql
    assert "observable_behavior" in sql


def test_v742_preserves_provenance_without_mass_yccd_mapping() -> None:
    sql = _sql()
    assert "SRC-CUR-MATH-2018" in sql
    assert "SRC-CUR-ENGLISH-2018" in sql
    assert "32/2018/TT-BGDĐT" in sql
    assert "learning_requirement_competency_links" not in sql
    assert "assessment_requirement_competency_links" not in sql


def test_v742_bridges_all_legacy_math_codes_to_canonical_owner() -> None:
    sql = _sql()
    for legacy_code in (
        "MATH-REASONING",
        "MATH-MODELING",
        "MATH-PROBLEM-SOLVING",
        "MATH-COMMUNICATION",
        "MATH-TOOLS",
    ):
        assert f"'{legacy_code}'" in sql
    assert sql.count('"canonical_owner":"competency_components"') == 5
    assert "public.canonical_entity_links" in sql
    assert "'COMPATIBILITY'" in sql


def test_v742_is_idempotent_and_transactional() -> None:
    sql = _sql().strip()
    assert sql.startswith("begin;")
    assert sql.endswith("commit;")
    assert sql.count("on conflict") >= 3
