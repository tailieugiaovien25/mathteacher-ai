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


def test_management_module_is_isolated_and_has_required_patch1_controls():
    text = MODULE.read_text(encoding="utf-8-sig")

    assert "Danh sách giáo án đã chuẩn hóa" in text
    assert '"Lựa chọn"' in text
    assert '"Chọn tất cả"' in text
    assert '"Bỏ chọn"' in text
    assert '"Xóa"' in text
    assert '"Tải xuống"' in text
    assert "_REGISTRY_KEY" in text
    assert "selected_standardized_lesson_plan_records" in text
    assert "không xóa giáo án đã lưu" in text.lower()


def test_weekly_schedule_wires_management_after_existing_download():
    text = WEEKLY.read_text(encoding="utf-8-sig")

    old_download = text.index(
        '"lbg_lesson_plan_download_"'
    )
    management_call = text.index(
        "render_standardized_lesson_plan_management("
    )
    technical_workspace = text.index(
        "def _render_weekly_schedule_technical_workspace("
    )

    assert old_download < management_call < technical_workspace


def test_patch1_has_no_merge_engine_or_persistence_mutation():
    text = MODULE.read_text(encoding="utf-8-sig")

    assert "supabase" not in text.casefold()
    assert "unlink(" not in text
