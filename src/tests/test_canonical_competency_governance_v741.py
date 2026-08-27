from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/migrations/202608270006_canonical_competency_governance.sql"
UI = ROOT / "src/portal_v2/ui/admin_competency_catalog_streamlit.py"
NAVIGATION = ROOT / "src/portal_v2/ui/admin_navigation.py"
SHELL = ROOT / "src/portal_v2/ui/admin_shell.py"


def test_migration_builds_multisubject_competency_backbone() -> None:
    text = MIGRATION.read_text(encoding="utf-8")
    for table in (
        "competency_frameworks",
        "competency_domains",
        "competency_components",
        "competency_indicators",
        "learning_requirement_competency_links",
        "competency_change_log",
    ):
        assert f"public.{table}" in text
    for group in ("QUALITY", "GENERAL", "SUBJECT_SPECIFIC", "DIGITAL", "AI"):
        assert group in text
    for strength in ("DIRECT", "INDIRECT", "CONTEXTUAL"):
        assert strength in text
    assert "save_learning_requirement_competency_link" in text
    assert "REQUIREMENT_COMPETENCY_GRADE_MISMATCH" in text


def test_default_domains_cover_math_english_digital_and_ai() -> None:
    text = MIGRATION.read_text(encoding="utf-8")
    for term in (
        "subject-math",
        "subject-foreign-language-1",
        "NL-MATH",
        "NL-ENG",
        "NL-DIGITAL",
        "NL-AI",
    ):
        assert term in text


def test_admin_writes_only_through_governed_rpc() -> None:
    text = UI.read_text(encoding="utf-8")
    assert "save_canonical_competency_entity" in text
    assert "save_learning_requirement_competency_link" in text
    for forbidden in (".insert(", ".update(", ".delete(", "service_role"):
        assert forbidden not in text


def test_admin_navigation_wires_competency_catalog() -> None:
    navigation = NAVIGATION.read_text(encoding="utf-8-sig")
    shell = SHELL.read_text(encoding="utf-8")
    assert 'ADMIN_PAGE_COMPETENCY_CATALOG = "competency_catalog"' in navigation
    assert '"Bộ mã năng lực"' in navigation
    assert "render_admin_competency_catalog" in shell


def test_migration_denies_direct_authenticated_writes() -> None:
    text = MIGRATION.read_text(encoding="utf-8")
    assert "revoke insert,update,delete" in text
    assert "current_user_is_portal_admin" in text
    assert "competency_change_log" in text
