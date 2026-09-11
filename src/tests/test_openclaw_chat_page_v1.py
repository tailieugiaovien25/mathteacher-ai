from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_openclaw_page_is_independent_and_wired_to_teacher_navigation() -> None:
    app = (ROOT / "scripts/teacher_portal/app.py").read_text(encoding="utf-8")
    page = (ROOT / "src/portal_v2/ui/openclaw_chat_streamlit.py").read_text(
        encoding="utf-8"
    )

    assert "'Trợ lý OpenClaw'," in app
    assert "elif selected == 'Trợ lý OpenClaw':" in app
    assert "render_openclaw_chat_page(" in app
    assert "authorized=authorization.can_access_admin_portal" in app
    assert 'PAGE_LABEL = "Trợ lý OpenClaw"' in page
    assert '"mathteacher-engineer", "main"' in page
    assert "openclaw_chat_form_v1" in page
    assert "if not authorized:" in page
    form_block = page.split('with st.form("openclaw_chat_form_v1"', 1)[1]
    submit_block = form_block.split("controls, _ =", 1)[0]
    assert "disabled=" not in submit_block


def test_openclaw_adapter_does_not_read_or_persist_gateway_token() -> None:
    adapter = (
        ROOT / "src/portal_v2/integrations/openclaw_cli.py"
    ).read_text(encoding="utf-8").lower()

    assert "gateway.auth.token" not in adapter
    assert "shell=false" in adapter
    assert "--message-file" in adapter
