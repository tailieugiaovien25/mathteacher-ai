from pathlib import Path
import ast


V2 = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py").read_text(encoding="utf-8")
WEEKLY = Path("src/portal_v2/ui/weekly_lesson_authoring_streamlit.py").read_text(encoding="utf-8")


def test_v2_has_canonical_utf8_labels():
    runtime_strings = {
        node.value
        for node in ast.walk(ast.parse(V2))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    for label in (
        "So\u1ea1n b\u00e0i c\u00f9ng chu\u1ea9n gi\u00e1o \u00e1n",
        "Tìm và tải giáo án từ máy (.docx)",
        "Chu\u1ea9n h\u00f3a",
        "L\u01b0u h\u1ec7 th\u1ed1ng",
        "Xem tr\u01b0\u1edbc gi\u00e1o \u00e1n g\u1ed1c",
    ):
        assert any(label in value for value in runtime_strings)
    for broken in ("So\u00e1\xba\xa1n", "M\u00c3\u00b4n", "L\u00e1\xbb"):
        assert broken not in V2


def test_snapshot_keeps_ids_and_adds_canonical_display():
    assert '"class_id": class_id' in WEEKLY
    assert '"class_display": class_display' in WEEKLY
    assert '"subject_ref": str(' in WEEKLY
    assert '"subject_display": (' in WEEKLY
    assert '_weekly_authoring_class_name(client=client' in WEEKLY
    assert '_weekly_authoring_subject_name(' in WEEKLY


def test_v2_prefers_display_values_with_id_fallback():
    assert 'context.get("subject_display") or context.get("subject_ref")' in V2
    assert 'item.get("class_display") or item.get("class_id")' in V2
