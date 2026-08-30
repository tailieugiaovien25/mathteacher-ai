from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MODULE = (
    ROOT
    / "src"
    / "portal_v2"
    / "ui"
    / "standardized_lesson_plan_management_streamlit.py"
)

WEEKLY = (
    ROOT
    / "src"
    / "portal_v2"
    / "ui"
    / "weekly_schedule_streamlit.py"
)


def test_patch2_row_actions_are_present():
    text = MODULE.read_text(encoding="utf-8-sig")

    assert '"Xem trước"' in text
    assert '"Lưu hệ thống"' in text
    assert '"Xóa"' in text
    assert '"Tải xuống"' in text
    assert '"Lựa chọn"' in text
    assert '"Chọn tất cả"' in text
    assert '"Bỏ chọn"' in text


def test_patch2_preview_reuses_injected_existing_renderer():
    text = MODULE.read_text(encoding="utf-8-sig")
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    assert "preview_html_builder" in text
    assert "preview_html_builder(content)" in text
    assert "preview_html_builder=build_document_html" in weekly


def test_patch2_save_reuses_one_existing_save_body():
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    assert (
        "def _save_standardized_artifact_to_library("
        in weekly
    )
    assert weekly.count(
        "upload_service.upload("
    ) == 1

    assert (
        "save_handler=_save_standardized_artifact_to_library"
        in weekly
    )


def test_existing_save_button_still_calls_shared_handler():
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    old_button = weekly.index(
        "save_standardized_clicked = st.button("
    )
    shared_handler = weekly.index(
        "def _save_standardized_artifact_to_library(",
        old_button,
    )
    old_button_dispatch = weekly.index(
        "if save_standardized_clicked:",
        shared_handler,
    )
    download_anchor = weekly.index(
        '<div id="download-standardized-lesson-plan"></div>',
        old_button_dispatch,
    )

    assert (
        old_button
        < shared_handler
        < old_button_dispatch
        < download_anchor
    )


def test_patch2_does_not_add_merge_engine_or_delete_persisted_files():
    text = MODULE.read_text(encoding="utf-8-sig")

    assert "supabase" not in text.casefold()
    assert "unlink(" not in text
    assert "os.remove" not in text
