from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/migrations/202608280001_canonical_learning_content_governance.sql"
UI = ROOT / "src/portal_v2/ui/admin_learning_content_catalog_streamlit.py"
NAVIGATION = ROOT / "src/portal_v2/ui/admin_navigation.py"
SHELL = ROOT / "src/portal_v2/ui/admin_shell.py"


def test_v75_builds_canonical_content_and_alignment_backbone() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for table in (
        "canonical_learning_content_units",
        "textbook_content_unit_links",
        "learning_requirement_content_links",
        "learning_content_change_log",
    ):
        assert f"public.{table}" in sql
    assert "assessment_content_context_catalog" in sql
    assert "learning_requirement_competency_links" in sql


def test_v75_keeps_canonical_content_independent_from_textbook_locations() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "content_unit_id text primary key" in sql
    assert "textbook_unit_id text not null references public.textbook_units" in sql
    assert "TEXTBOOK_CONTENT_SCOPE_MISMATCH" in sql
    assert "REQUIREMENT_CONTENT_SCOPE_MISMATCH" in sql


def test_v75_governed_rpc_and_rls_contract() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for rpc in (
        "save_canonical_learning_content",
        "save_textbook_content_unit_link",
        "save_learning_requirement_content_link",
    ):
        assert rpc in sql
    assert sql.count("current_user_is_portal_admin") >= 4
    assert "revoke insert,update,delete" in sql
    assert "learning_content_change_log" in sql


def test_v75_admin_uses_rpc_only_for_writes() -> None:
    text = UI.read_text(encoding="utf-8")
    for rpc in (
        "save_canonical_learning_content",
        "save_textbook_content_unit_link",
        "save_learning_requirement_content_link",
    ):
        assert rpc in text
    for forbidden in (".insert(", ".update(", ".delete(", "service_role"):
        assert forbidden not in text


def test_v75_admin_navigation_is_wired() -> None:
    navigation = NAVIGATION.read_text(encoding="utf-8-sig")
    shell = SHELL.read_text(encoding="utf-8")
    assert 'ADMIN_PAGE_LEARNING_CONTENT_CATALOG = "learning_content_catalog"' in navigation
    assert '"Nội dung dạy học"' in navigation
    assert "render_admin_learning_content_catalog" in shell


def test_v75_models_textbook_and_requirement_alignment_semantics() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for term in (
        "PRIMARY_LOCATION", "PRACTICE_LOCATION", "FULL", "PARTIAL",
        "PREREQUISITE", "EXTENSION", "DIRECT", "INDIRECT", "CONTEXTUAL",
    ):
        assert term in sql
