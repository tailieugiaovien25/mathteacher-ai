from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608270003_assessment_blueprint_cell_authoring.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").lower()


def test_cell_replacement_is_atomic_and_teacher_owned() -> None:
    sql = _sql()
    assert "replace_assessment_blueprint_cells" in sql
    assert "assessment_blueprint_version_is_editable" in sql
    assert "delete from public.assessment_blueprint_cells" in sql
    assert "insert into public.assessment_blueprint_cells" in sql
    assert sql.index("delete from public.assessment_blueprint_cells") < (
        sql.index("insert into public.assessment_blueprint_cells")
    )


def test_cell_rpc_enforces_profile_curriculum_and_level_totals() -> None:
    sql = _sql()
    for contract in (
        "blueprint_cell_scope_invalid",
        "blueprint_cell_section_totals_mismatch",
        "blueprint_cell_level_totals_mismatch",
        "assessment_profile_sections",
        "assessment_profile_level_allocations",
        "assessment_curriculum_topics",
        "assessment_cognitive_levels",
    ):
        assert contract in sql


def test_review_rpc_preserves_database_review_trigger_governance() -> None:
    sql = _sql()
    assert "review_assessment_blueprint" in sql
    assert "current_user_is_portal_admin" in sql
    assert "insert into public.assessment_blueprint_reviews" in sql
    assert "(select auth.uid())" in sql
    assert "grant execute on function" in sql
    assert "to authenticated" in sql
    assert "to anon" not in sql
