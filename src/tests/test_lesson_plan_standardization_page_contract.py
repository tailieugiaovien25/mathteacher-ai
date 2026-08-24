from pathlib import Path


APP = Path("scripts/teacher_portal/app.py")
PAGE = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")


def app_source() -> str:
    return APP.read_text(encoding="utf-8-sig")


def page_source() -> str:
    return PAGE.read_text(encoding="utf-8-sig")


def test_portal_keeps_restored_authoring_and_standardization_pages():
    text = app_source()

    assert (
        "Chuẩn hóa giáo án" in text
        or "Chu\\u1ea9n h\\xf3a gi\\xe1o \\xe1n" in text
    )
    assert (
        "Công cụ soạn bài" in text
        or "C\\xf4ng c\\u1ee5 so\\u1ea1n b\\xe0i" in text
    )
    assert "Chu\\u1ea9n gi\\xe1o \\xe1n" not in text
    assert "L\\u1ecbch b\\xe1o gi\\u1ea3ng & PBSDTB" in text
    assert "lesson_plan_standardization_page" not in text
    assert "render_weekly_schedule_workspace(" in text
    assert "render_lesson_authoring_tools_workspace(" in text
    assert "render_weekly_schedule_and_equipment_workspace(" in text
    assert "user_id=str(user_id)" in text


def test_restored_authoring_page_has_independent_focus_and_title():
    text = page_source()

    assert "def render_lesson_authoring_tools_workspace(" in text
    assert 'initial_focus="AI"' in text
    assert 'workspace_page_key="AUTHORING_TOOLS"' in text
    assert 'page_title="Công cụ soạn bài"' in text
    assert 'initial_focus: str = "STANDARDIZE"' in text
    assert 'workspace_page_key: str = "STANDARDIZATION"' in text
    assert "lesson_authoring_workspace_page_key" in text
    assert "{escape(page_title)}" in text


def test_renamed_workspace_uses_existing_standardization_workflow():
    text = page_source()

    assert "Chuẩn hóa giáo án" in text
    assert "_render_lesson_authoring_tool_hub(" in text
    assert "_render_lesson_plan_standardization_workspace(" in text
    assert "CHU\\u1ea8N H\\u00d3A GI\\u00c1O \\u00c1N" in text


def test_standardization_workspace_restores_five_real_action_buttons():
    text = page_source()

    assert (
        "def _render_standardization_action_flow("
        in text
    )

    required_keys = (
        "standardization_action_upload",
        "standardization_action_create",
        "standardization_action_preview",
        "standardization_action_save",
        "standardization_action_download",
    )

    for key in required_keys:
        assert key in text

    assert (
        "lesson_plan_standardization_action"
        in text
    )

    assert (
        "st.button("
        in text
    )

    # AI-006E.2:
    # The action bar must use real Streamlit controls.
    # Do not regress to HTML anchor-only navigation.
    assert (
        'href="#upload-lesson-plan"'
        not in text
    )

def test_schedule_equipment_page_remains_two_part_workspace():
    text = page_source()

    assert '"1. Lịch báo giảng"' in text
    assert '"2. Phiếu báo sử dụng thiết bị"' in text
    assert "LỊCH BÁO GIẢNG &amp; PBSDTB" in text
    assert "Một tuần dữ liệu · Hai biểu mẫu đồng bộ" in text
    assert "_render_weekly_schedule_technical_workspace(" in text
    assert "_render_lesson_plan_standardization_workspace(" in text
    assert "_render_equipment_usage_report(" in text


def test_protected_pages_keep_their_existing_renderers():
    text = app_source()

    assert "render_lesson_authoring_ai_page(" in text
    assert "render_weekly_schedule_and_equipment_workspace(" in text
    assert "render_lesson_authoring_tools_workspace(" in text
