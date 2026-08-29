from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "scripts" / "teacher_portal" / "app.py"


def test_confirmed_sign_in_completes_pending_registration_before_role_denial():
    text = APP.read_text(encoding="utf-8-sig")

    assert "def complete_authenticated_portal_registration(" in text
    assert "client.auth.get_user()" in text
    assert 'metadata.get("full_name"' in text
    assert '"create_or_refresh_own_portal_registration"' in text
    assert "def prepare_authenticated_portal_access(" in text

    prepare_call = text.index(
        "portal_role = prepare_authenticated_portal_access("
    )
    repository_call = text.index(
        "connect_feature_repositories(st.session_state, client, user_id)",
        prepare_call,
    )
    assert prepare_call < repository_call


def test_inactive_trusted_account_is_not_reregistered():
    text = APP.read_text(encoding="utf-8-sig")
    start = text.index("def prepare_authenticated_portal_access(")
    end = text.index("def build_current_portal_authorization(", start)
    function = text[start:end]

    trusted_guard = function.index("if resolution.trusted:")
    registration_call = function.index(
        "if complete_authenticated_portal_registration(client=client):"
    )
    assert trusted_guard < registration_call
    assert "Tài khoản đã ngừng hoạt động" in function


def test_registration_bridge_never_grants_a_portal_role():
    text = APP.read_text(encoding="utf-8-sig")
    start = text.index("def complete_authenticated_portal_registration(")
    end = text.index("def prepare_authenticated_portal_access(", start)
    function = text[start:end]

    assert 'client.table("portal_roles")' not in function
    assert '"review_portal_user_registration"' not in function
    assert "APPROVED" not in function
