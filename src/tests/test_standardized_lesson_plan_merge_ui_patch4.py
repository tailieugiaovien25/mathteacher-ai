from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/portal_v2/ui/standardized_lesson_plan_management_streamlit.py"

def _text():
    return MODULE.read_text(encoding="utf-8-sig")

def test_merge_service_wired():
    text = _text()
    assert "LessonPlanMergeService" in text
    assert "LessonPlanMergeSource" in text
    assert ".merge(" in text

def test_merge_ui_controls():
    text = _text()
    for token in ('"Gộp giáo án"', '"GỘP FILE"', '"↑"', '"↓"', "_MERGE_ORDER_KEY"):
        assert token in text

def test_merged_actions_and_provenance():
    text = _text()
    for token in ('"#### File giáo án đã gộp"', '"Xem trước"', '"Tải file Word"', '"Nguồn gộp: "'):
        assert token in text
    assert '" → ".join(' in text

def test_merged_save_visible_but_disabled():
    text = _text()
    pos = text.index('"standardized_merge_save_disabled_v4"')
    nearby = text[pos-250:pos+450]
    assert '"Lưu hệ thống"' in nearby
    assert "disabled=True" in nearby
    assert "provenance" in nearby

def test_locked_labels_preserved():
    text = _text()
    for token in (
        '"Danh sách giáo án đã chuẩn hóa"', '"Lựa chọn"', '"Chọn tất cả"',
        '"Bỏ chọn"', '"Xem trước"', '"Lưu hệ thống"', '"Xóa"', '"Tải xuống"',
    ):
        assert token in text

def test_utf8_not_damaged():
    text = _text()
    assert "\ufffd" not in text
    for damaged in ("G?P FILE", "g?p giáo án", "Xem tru?c", "Luu h? th?ng", "B? ch?n", "L?a ch?n"):
        assert damaged not in text

def test_no_direct_storage_or_destructive_delete():
    text = _text()
    assert "supabase" not in text.casefold()
    assert "unlink(" not in text
    assert "os.remove" not in text
