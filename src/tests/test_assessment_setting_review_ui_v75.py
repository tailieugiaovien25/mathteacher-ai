from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src/portal_v2/ui/assessment_exam_settings_streamlit.py"
ADMIN_UI = ROOT / "src/portal_v2/ui/admin_assessment_setting_review_streamlit.py"
NAV = ROOT / "src/portal_v2/ui/admin_navigation.py"
SHELL = ROOT / "src/portal_v2/ui/admin_shell.py"
MIGRATION = (
    ROOT
    / "supabase/migrations/202608280006_admin_any_user_assessment_review.sql"
)


def test_user_settings_page_can_save_and_submit_for_review() -> None:
    text = UI.read_text(encoding="utf-8")
    assert "Lưu bản nháp thiết đặt" in text
    assert "Gửi thiết đặt để duyệt" in text
    assert "submit_assessment_exam_setting_for_review" in text


def test_current_ui_does_not_block_admin_same_owner_review() -> None:
    text = UI.read_text(encoding="utf-8")
    assert "ADMIN không được tự duyệt thiết đặt do mình sở hữu." not in text
    assert "disabled=own_setting" not in text


def test_admin_has_dedicated_assessment_review_page() -> None:
    nav = NAV.read_text(encoding="utf-8")
    shell = SHELL.read_text(encoding="utf-8")
    admin_ui = ADMIN_UI.read_text(encoding="utf-8")
    assert 'ADMIN_PAGE_ASSESSMENT_REVIEWS = "assessment_reviews"' in nav
    assert '"Duyệt đề kiểm tra"' in nav
    assert "ADMIN_PAGE_ASSESSMENT_REVIEWS" in shell
    assert "render_admin_assessment_setting_review" in shell
    assert "pending_reviews()" in admin_ui
    assert "catalog.review(" in admin_ui


def test_admin_review_page_requires_note_for_revision_or_rejection() -> None:
    text = ADMIN_UI.read_text(encoding="utf-8")
    assert '{"REVISION_REQUIRED", "REJECTED"}' in text
    assert "phải có nhận xét của ADMIN" in text


def test_superseding_migration_allows_admin_same_owner_review_safely() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "assessment_setting_self_review_forbidden" not in sql
    assert "current_user_is_portal_admin" in sql
    assert "pending_review" in sql
    assert "reviewer_user_id" in sql
    for decision in ("approved", "revision_required", "rejected"):
        assert decision in sql