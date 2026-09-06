from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "src" / "portal_v2" / "ui" / "admin_canonical_code_catalog_streamlit.py"
CENTER = ROOT / "src" / "portal_v2" / "ui" / "admin_lesson_plan_coordination_center_streamlit.py"


def test_center_keeps_legacy_heading_contract():
    text = CENTER.read_text(encoding="utf-8")
    assert 'st.subheader("Chính sách nhóm giáo án")' in text
    assert "render_admin_lesson_plan_grouping_policy(st, client=client)" in text


def test_business_mode_labels_are_vietnamese():
    text = CATALOG.read_text(encoding="utf-8")
    assert '"Soạn theo tiết": LessonPlanGroupingMode.BY_PERIOD' in text
    assert '"Soạn theo bài": LessonPlanGroupingMode.BY_LESSON' in text
    assert '"Soạn theo tuần": LessonPlanGroupingMode.BY_WEEK' in text


def test_table_uses_business_labels():
    text = CATALOG.read_text(encoding="utf-8")
    assert '"Cách soạn": mode_display.get(item.mode, item.mode.value)' in text
    assert '"Đang áp dụng" if item.active else "Ngừng áp dụng"' in text


def test_canonical_refs_are_preserved_for_save():
    text = CATALOG.read_text(encoding="utf-8")
    assert "subject_ref=str(subject_ref)" in text
    assert "component_ref=component_code" in text
    assert "policy_repo.upsert_config" in text
    assert "READ_AFTER_WRITE_POLICY_NOT_FOUND" in text


def test_no_by_grade_claim_in_grouping_renderer():
    text = CATALOG.read_text(encoding="utf-8")
    start = text.index("def _render_admin_lesson_plan_grouping_policy")
    end = text.index("def render_admin_canonical_code_catalog", start)
    block = text[start:end]
    assert "BY_GRADE" not in block
    assert "Theo khối" not in block