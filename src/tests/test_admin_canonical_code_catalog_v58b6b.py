import inspect
from portal_v2.ui import admin_navigation, admin_shell
from portal_v2.ui import admin_canonical_code_catalog_streamlit as ui

def test_navigation_contains_canonical_code_management():
    assert "Quản trị Bộ mã Canonical" in admin_navigation.admin_portal_page_labels()
    assert hasattr(admin_navigation,"ADMIN_PAGE_CANONICAL_CODE_CATALOG")

def test_admin_shell_routes_canonical_code_management():
    source=inspect.getsource(admin_shell)
    assert "render_admin_canonical_code_catalog" in source
    assert "ADMIN_PAGE_CANONICAL_CODE_CATALOG" in source

def test_ui_uses_supabase_registry_and_is_non_destructive():
    source=inspect.getsource(ui)
    assert "SupabaseCanonicalCodeRepository" in source
    assert "list_codes()" in source
    assert "st.dataframe" in source
    assert ".delete(" not in source
