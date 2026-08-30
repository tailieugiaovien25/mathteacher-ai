import inspect
from portal_v2.context.supabase_canonical_code_repository import SupabaseCanonicalCodeRepository
from portal_v2.ui import admin_canonical_code_catalog_streamlit as ui

def test_lifecycle_repository_has_no_delete_path():
    source=inspect.getsource(SupabaseCanonicalCodeRepository)
    assert "update_code_lifecycle" in source
    assert ".update(payload)" in source
    assert ".delete(" not in source

def test_lifecycle_only_allows_active_inactive():
    source=inspect.getsource(SupabaseCanonicalCodeRepository.update_code_lifecycle)
    assert '{"ACTIVE", "INACTIVE"}' in source
    assert '"namespace"' in source and '"code"' in source

def test_admin_ui_exposes_add_and_lifecycle_without_delete():
    source=inspect.getsource(ui)
    assert 'st.subheader("Thêm mã mới")' in source
    assert 'st.subheader("Điều chỉnh vòng đời mã")' in source
    assert "update_code_lifecycle(" in source
    assert "Canonical code/ID không bị thay đổi" in source
    assert ".delete(" not in source
