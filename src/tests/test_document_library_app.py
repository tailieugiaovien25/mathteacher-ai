import pytest

from scripts.document_library.app import (
    authenticate,
    build_document,
    comma_values,
    document_rows,
    drive_reference,
    google_oauth_settings,
    supabase_settings,
    validate_oauth_callback,
)
from teacher_document_library_v2 import DocumentCategory


def test_public_supabase_settings_require_both_values():
    assert supabase_settings({}) is None
    assert supabase_settings({"SUPABASE_URL": "https://example.supabase.co"}) is None
    assert supabase_settings({
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
    }) == ("https://example.supabase.co", "sb_publishable_test")


def test_authentication_scopes_repository_to_returned_user():
    class Auth:
        def sign_in_with_password(self, credentials):
            assert credentials["email"] == "teacher@example.com"
            user = type("User", (), {"id": "user-123"})()
            return type("Response", (), {"user": user})()

    repository = authenticate(type("Client", (), {"auth": Auth()})(), " teacher@example.com ", "password")
    assert repository._user_id == "user-123"


def test_build_document_registers_google_drive_reference():
    document = build_document(
        title="Giáo án Tập hợp", category=DocumentCategory.LESSON_PLAN,
        academic_year="2026-2027", subject="Toán", grade_level="6",
        class_name="6A1", file_name="giao-an.docx", mime_type="application/docx",
        drive_link_or_id="https://drive.google.com/file/d/drive-file-123/view",
        description="Bản đã chuẩn hóa", tags="học kỳ 1, đã chuẩn hóa, học kỳ 1",
    )
    assert document.storage_file_id == "drive-file-123"
    assert document.tags == ("học kỳ 1", "đã chuẩn hóa")
    assert document_rows((document,))[0]["Loại"] == "Giáo án"
    assert comma_values("Toán, Âm nhạc, Toán") == ("Toán", "Âm nhạc")


def test_drive_reference_rejects_unrelated_websites():
    with pytest.raises(ValueError, match="Google"):
        drive_reference("https://example.com/file.docx")


def test_ui_keeps_provider_sdk_outside_catalog_service():
    import inspect
    from teacher_document_library_v2.services import TeacherDocumentCatalog

    source = inspect.getsource(TeacherDocumentCatalog).lower()
    assert "supabase" not in source
    assert "google" not in source
    assert "streamlit" not in source


def test_google_oauth_settings_are_read_from_environment():
    assert google_oauth_settings({}) is None
    settings = google_oauth_settings({
        "GOOGLE_OAUTH_CLIENT_ID": "client-id",
        "GOOGLE_OAUTH_CLIENT_SECRET": "client-secret",
        "GOOGLE_OAUTH_REDIRECT_URI": "http://localhost:8501",
    })
    assert settings.client_id == "client-id"


def test_oauth_callback_rejects_state_mismatch_and_empty_code():
    from teacher_document_library_v2.adapters import create_signed_oauth_state

    state = create_signed_oauth_state("secret", now=1000)
    with pytest.raises(ValueError, match="Trạng thái"):
        validate_oauth_callback(incoming_state=state + "x", signing_key="secret", code="code")
    with pytest.raises(ValueError, match="mã cấp quyền"):
        validate_oauth_callback(
            incoming_state=create_signed_oauth_state("secret"),
            signing_key="secret",
            code="",
        )
