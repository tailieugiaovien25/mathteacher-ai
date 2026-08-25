from pathlib import Path


ADMIN_SHELL = Path("src/portal_v2/ui/admin_shell.py")
ASSIGNMENT_UI = Path(
    "src/portal_v2/ui/admin_assignment_workspace_streamlit.py"
)
ROLE_SOURCE = Path(
    "src/portal_v2/authorization/supabase_portal_role_source.py"
)
LOGIN_APP = Path("scripts/teacher_portal/app.py")
MIGRATION = Path(
    "supabase/migrations/202608250001_admin_user_account_status.sql"
)


def test_user_page_has_account_actions_and_statuses():
    text = ADMIN_SHELL.read_text(encoding="utf-8-sig")
    assert 'st.title("Người dùng & Quyền hạn")' in text
    assert '"Đang có hiệu lực"' in text
    assert '"Ngừng hoạt động"' in text
    assert '"Chỉnh sửa"' in text
    assert '"Phân công"' in text
    assert 'toggle_label = "Ngừng" if item["is_active"] else "Kích hoạt"' in text


def test_assignment_action_deep_links_selected_teacher():
    shell = ADMIN_SHELL.read_text(encoding="utf-8-sig")
    assignment = ASSIGNMENT_UI.read_text(encoding="utf-8-sig")
    assert '"admin_assignment_target_teacher_id"' in shell
    assert '"admin_portal_navigation_target"' in shell
    assert '"admin_assignment_target_teacher_id"' in assignment
    assert '"admin_assignment_row_teacher"' in assignment


def test_inactive_account_is_rejected_during_portal_login():
    source = ROLE_SOURCE.read_text(encoding="utf-8-sig")
    app = LOGIN_APP.read_text(encoding="utf-8-sig")
    assert '.select("user_id,role,is_active")' in source
    assert "if not resolution.can_access_portal:" in app


def test_migration_allows_only_admin_teacher_status_updates():
    sql = MIGRATION.read_text(encoding="utf-8-sig").lower()
    assert "add column if not exists is_active" in sql
    assert '"admins_update_teacher_account_status"' in sql
    assert "role = 'teacher'" in sql
    assert "grant update (is_active)" in sql
