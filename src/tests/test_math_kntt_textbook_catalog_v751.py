from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/202608280002_math_kntt_textbook_catalog.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_v751_registers_eight_books_as_versioned_restricted_sources() -> None:
    sql = _sql()
    assert "generate_series(6,9)" in sql
    assert "generate_series(1,2)" in sql
    assert "'RESTRICTED','AUTHORIZED_USERS'" in sql
    assert "public.educational_source_versions" in sql
    assert "MATH-KNTT" in sql


def test_v751_catalog_is_math_first_and_multigrade() -> None:
    sql = _sql()
    assert "'subject-math'" in sql
    assert "'program-vn-gdpt-2018'" in sql
    for grade in range(6, 10):
        for volume in (1, 2):
            assert f"textbook-math-kntt-g'||grade_number||'-v'||volume_number" in sql
        assert f"({grade},1," in sql
        assert f"({grade},2," in sql


def test_v751_seeds_exact_chapter_count_and_stable_codes() -> None:
    sql = _sql()
    chapter_rows = [
        line.strip()
        for line in sql.splitlines()
        if line.strip().startswith("(") and line.count(",") >= 3
        and line.strip()[1:2] in {"6", "7", "8", "9"}
    ]
    assert len(chapter_rows) == 39
    assert "MATH-KNTT-G'||grade_number||'-CH'" in sql
    assert "unit-math-kntt-g'||grade_number||'-chapter-'" in sql


def test_v751_covers_expected_grade_chapter_ranges() -> None:
    sql = _sql()
    expected = {
        6: (1, 9),
        7: (1, 10),
        8: (1, 10),
        9: (1, 10),
    }
    for grade, (first, last) in expected.items():
        assert f"({grade},1,{first}," in sql
        assert f"({grade},2,{last}," in sql


def test_v751_does_not_embed_copyrighted_lesson_payloads() -> None:
    sql = _sql()
    assert '"copyrighted_full_text_included",false' not in sql
    assert "'copyrighted_full_text_included',false" in sql
    assert "'full_text_stored',false" in sql
    assert "assessment_learning_requirements" not in sql
    assert "learning_requirement_content_links" not in sql


def test_v751_is_idempotent_and_transactional() -> None:
    sql = _sql().strip()
    assert sql.startswith("begin;")
    assert sql.endswith("commit;")
    assert sql.count("on conflict") == 4
