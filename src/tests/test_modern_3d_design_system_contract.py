from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_portal_installs_one_shared_modern_3d_design_system():
    app = (ROOT / "scripts/teacher_portal/app.py").read_text(
        encoding="utf-8-sig"
    )
    styles = (
        ROOT / "src/portal_v2/ui/modern_3d_design_system.py"
    ).read_text(encoding="utf-8-sig")

    assert "apply_modern_3d_design_system(st)" in app
    assert "MODERN_3D_DESIGN_SYSTEM_CSS" in styles
    assert '[data-testid="stSidebar"]' in styles
    assert '[data-testid="stForm"]' in styles
    assert '[data-testid="stFileUploaderDropzone"]' in styles
    assert '[data-testid="stDataFrame"]' in styles
    assert "prefers-reduced-motion" in styles


def test_login_uses_the_shared_three_dimensional_scene():
    app = (ROOT / "scripts/teacher_portal/app.py").read_text(
        encoding="utf-8-sig"
    )

    assert 'class="mt-login-scene"' in app
    assert 'class="mt-login-title"' in app
    assert 'with st.form("portal_login")' in app
    assert 'st.form_submit_button("Đăng nhập"' in app

    styles = (
        ROOT / "src/portal_v2/ui/modern_3d_design_system.py"
    ).read_text(encoding="utf-8-sig")
    assert ':has(.mt-login-scene)' in styles


def test_visual_layer_does_not_replace_existing_widget_keys():
    app = (ROOT / "scripts/teacher_portal/app.py").read_text(
        encoding="utf-8-sig"
    )
    styles = (
        ROOT / "src/portal_v2/ui/modern_3d_design_system.py"
    ).read_text(encoding="utf-8-sig")

    assert 'key="portal_navigation"' in app
    assert 'st.sidebar.button("Đăng xuất"' in app
    assert "session_state" not in styles
    assert "st.button(" not in styles
