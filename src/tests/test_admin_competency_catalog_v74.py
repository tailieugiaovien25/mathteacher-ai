import inspect
from portal_v2.ui import admin_navigation
from portal_v2.ui import admin_shell
from portal_v2.ui import admin_competency_catalog_streamlit

def test_admin_navigation_contains_competency_catalog():
    assert admin_navigation.ADMIN_PAGE_COMPETENCY_CATALOG in admin_navigation.admin_portal_page_ids()
    assert "Mã năng lực" in admin_navigation.admin_portal_page_labels()

def test_admin_shell_routes_competency_catalog():
    source=inspect.getsource(admin_shell)
    assert "render_admin_competency_catalog" in source
    assert "ADMIN_PAGE_COMPETENCY_CATALOG" in source

def test_admin_competency_ui_preserves_id_and_status_lifecycle():
    source=inspect.getsource(admin_competency_catalog_streamlit)
    assert "ID bất biến" in source
    assert "DEPRECATED" in source
    assert "provenance" in source.lower()
    assert "delete(" not in source
