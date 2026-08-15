import inspect

from teacher_document_library_v2.adapters.google_drive_oauth import (
    DRIVE_FILE_SCOPE,
    GoogleDriveFileStorage,
    GoogleOAuthSettings,
    create_signed_oauth_state,
    credentials_to_dict,
    derive_code_verifier,
    validate_signed_oauth_state,
)


def test_oauth_settings_require_client_id_and_secret():
    assert GoogleOAuthSettings.from_environment({}) is None
    assert GoogleOAuthSettings.from_environment({"GOOGLE_OAUTH_CLIENT_ID": "id"}) is None
    settings = GoogleOAuthSettings.from_environment(
        {"GOOGLE_OAUTH_CLIENT_ID": " id ", "GOOGLE_OAUTH_CLIENT_SECRET": " secret "}
    )
    assert settings.redirect_uri == "http://localhost:8501"
    assert settings.client_config()["web"]["redirect_uris"] == ["http://localhost:8501"]


def test_credentials_are_serialized_for_session_memory():
    credentials = type(
        "Credentials",
        (),
        {
            "token": "access",
            "refresh_token": "refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "id",
            "client_secret": "secret",
            "scopes": [DRIVE_FILE_SCOPE],
        },
    )()
    assert credentials_to_dict(credentials)["scopes"] == [DRIVE_FILE_SCOPE]


def test_drive_scope_is_minimal_and_adapter_has_no_token_file_persistence():
    assert DRIVE_FILE_SCOPE.endswith("/auth/drive.file")
    source = inspect.getsource(
        __import__(
            "teacher_document_library_v2.adapters.google_drive_oauth",
            fromlist=["placeholder"],
        )
    ).lower()
    for forbidden in ("token.json", "pickle", "write_text", "open("):
        assert forbidden not in source


def test_file_name_removes_windows_and_unix_paths():
    assert GoogleDriveFileStorage._safe_file_name(r"C:\\temp\\giao-an.docx") == "giao-an.docx"
    assert GoogleDriveFileStorage._safe_file_name("../de-kiem-tra.pdf") == "de-kiem-tra.pdf"


def test_signed_state_survives_new_streamlit_session_and_expires():
    state = create_signed_oauth_state("secret", now=1000)
    validate_signed_oauth_state(state, "secret", now=1050)

    import pytest

    with pytest.raises(ValueError, match="invalid"):
        validate_signed_oauth_state(state, "different-secret", now=1050)
    with pytest.raises(ValueError, match="expired"):
        validate_signed_oauth_state(state, "secret", now=2000)


def test_pkce_verifier_is_recreated_from_signed_state():
    state = create_signed_oauth_state("secret", now=1000)
    first = derive_code_verifier(state, "secret")
    second = derive_code_verifier(state, "secret")

    assert first == second
    assert len(first) >= 43
    assert derive_code_verifier(state, "other-secret") != first
