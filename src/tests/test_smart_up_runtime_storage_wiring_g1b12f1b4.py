from pathlib import Path

UI = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")


def source():
    return UI.read_text(encoding="utf-8-sig")


def test_runtime_storage_binding_uses_existing_session_storage():
    text = source()
    assert "SMART_UP_RUNTIME_STORAGE_BINDING" in text
    assert 'st.session_state.get("document_library_storage")' in text
    assert 'getattr(runtime_storage, "download", None)' in text


def test_runtime_binding_is_read_only_download_only():
    text = source()
    start = text.index("# SMART_UP_RUNTIME_STORAGE_BINDING")
    end = text.index("# Smart Up discovery is read-only", start)
    block = text[start:end]
    assert "runtime_storage.download(" in block
    assert "runtime_storage.upload(" not in block
    assert "runtime_storage.delete(" not in block


def test_runtime_loader_downloads_candidate_storage_file_id():
    text = source()
    assert "document.storage_file_id" in text


def test_auto_preview_hook_remains_present():
    text = source()
    assert "SMART_UP_AUTO_PREVIEW_LOAD" in text
    assert "st.session_state[ORIGINAL_DOCUMENT_KEY]" in text
    assert '"source": "SMART_UP"' in text
    assert '"storage_provider": best.document.storage_provider' in text
    assert '"storage_file_id": best.document.storage_file_id' in text
    assert '"match_reason": best.match_reason' in text