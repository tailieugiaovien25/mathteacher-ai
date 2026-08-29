from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SHELL = ROOT / "src/portal_v2/ui/admin_shell.py"
ASSIGNMENT = ROOT / "src/portal_v2/ui/admin_assignment_workspace_streamlit.py"
MIGRATION = ROOT / "supabase/migrations/202608290001_bootstrap_doancongtuyen_full_access.sql"


def test_admin_with_teacher_profile_appears_in_user_directory():
    text = SHELL.read_text(encoding="utf-8-sig")
    assert '.in_("role", ("teacher", "admin"))' in text
    assert '"role": str(role_row.get("role"' in text


def test_active_admin_is_available_for_professional_assignment():
    text = ASSIGNMENT.read_text(encoding="utf-8-sig")
    assert '.in_("role", ("teacher", "admin"))' in text
    assert '.eq("is_active", True)' in text


def test_admin_account_cannot_be_disabled_from_teacher_user_row():
    text = SHELL.read_text(encoding="utf-8-sig")
    assert 'is_protected_admin = item["role"] == "admin"' in text
    assert 'disabled=is_protected_admin or not bool(item["full_name"])' in text


def test_target_migration_is_exact_and_complete():
    text = MIGRATION.read_text(encoding="utf-8-sig")
    assert text.count("doancongtuyen@gmail.com") == 1
    assert "TARGET_AUTH_USER_NOT_FOUND" in text
    assert "values (v_user.id, 'admin', true)" in text
    for field in (
        "teacher_code", "full_name", "school_name", "subjects",
        "grade_levels", "default_academic_year",
    ):
        assert field in text


def test_target_email_is_not_hard_coded_in_application_files():
    assert "doancongtuyen@gmail.com" not in SHELL.read_text(
        encoding="utf-8-sig"
    ).lower()
    assert "doancongtuyen@gmail.com" not in ASSIGNMENT.read_text(
        encoding="utf-8-sig"
    ).lower()
