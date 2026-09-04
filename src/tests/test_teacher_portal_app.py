from scripts.teacher_portal.app import (
    PORTAL_PAGES,
    authenticate_portal,
    build_teacher_profile,
    clear_portal_session,
    connect_feature_repositories,
    has_complete_portal_session,
    select_portal_page,
    supabase_settings,
)


def test_portal_requires_both_public_supabase_values():
    assert supabase_settings({}) is None
    assert supabase_settings({"SUPABASE_URL": "https://example.supabase.co"}) is None
    assert supabase_settings({
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
    }) == ("https://example.supabase.co", "sb_publishable_test")


def test_portal_authentication_returns_one_shared_identity():
    class Auth:
        def sign_in_with_password(self, credentials):
            assert credentials == {"email": "teacher@example.com", "password": "pass"}
            user = type("User", (), {"id": "user-123", "email": "teacher@example.com"})()
            return type("Response", (), {"user": user})()

    assert authenticate_portal(
        type("Client", (), {"auth": Auth()})(), " teacher@example.com ", "pass"
    ) == ("user-123", "teacher@example.com")


def test_portal_connects_feature_adapters_to_same_user():
    state = {}
    client = object()
    connect_feature_repositories(state, client, "user-123")
    assert state["portal_supabase_client"] is client
    assert state["weekly_supabase_repository"].user_id == "user-123"
    assert state["document_library_repository"]._user_id == "user-123"
    assert "notification_repository" in state
    assert (
        state["notification_repository"]._owner_id
        == "user-123"
    )


def test_portal_logout_clears_shared_and_feature_sessions():
    state = {
        "portal_supabase_client": object(),
        "portal_user_id": "user-123",
        "weekly_supabase_repository": object(),
        "document_library_repository": object(),
        "portal_flash_feedback": object(),
        "google_drive_credentials": {},
        "unrelated": "keep",
    }
    clear_portal_session(state)
    assert state == {"unrelated": "keep"}


def test_dashboard_navigation_updates_page_and_sidebar_choice():
    state = {}
    select_portal_page(state, "Kho tài liệu")
    assert state == {"portal_navigation_request": "Kho tài liệu"}


def test_portal_builds_normalized_teacher_profile():
    profile = build_teacher_profile(
        teacher_code=" GV001 ", full_name=" Nguyễn Văn A ",
        school_name=" THCS Mẫu ", subjects="Toán, Tin học, Toán",
        grade_levels="6, 7", default_academic_year="2026-2027",
        show_teacher_name=True, show_school_name=True,
    )
    assert profile.teacher_code == "GV001"
    assert profile.subjects == ("Toán", "Tin học")
    assert "Kho tài liệu" in PORTAL_PAGES
    assert "Công cụ soạn bài" not in PORTAL_PAGES
    assert "Soạn bài cùng chuẩn giáo án" in PORTAL_PAGES
    assert "Soạn bài cùng AI" in PORTAL_PAGES
    assert "Lịch báo giảng & PBSDTB" in PORTAL_PAGES


def test_feature_apps_support_embedded_rendering():
    import inspect
    from scripts.document_library.app import main as document_main
    from scripts.weekly_schedule.app import main as weekly_main
    from scripts.word_standardizer.app import main as word_main

    for function in (document_main, weekly_main, word_main):
        assert "embedded" in inspect.signature(function).parameters



def test_portal_session_requires_complete_identity():
    client = object()

    assert has_complete_portal_session(
        {
            "portal_supabase_client": client,
            "portal_user_id": "user-123",
            "portal_user_email": "teacher@example.com",
        }
    )

    assert not has_complete_portal_session(
        {
            "portal_supabase_client": client,
            "portal_user_id": "user-123",
        }
    )

    assert not has_complete_portal_session(
        {
            "portal_supabase_client": client,
            "portal_user_email": "teacher@example.com",
        }
    )

    assert not has_complete_portal_session(
        {
            "portal_user_id": "user-123",
            "portal_user_email": "teacher@example.com",
        }
    )


def test_portal_session_rejects_blank_email():
    assert not has_complete_portal_session(
        {
            "portal_supabase_client": object(),
            "portal_user_id": "user-123",
            "portal_user_email": "",
        }
    )
