import pytest

from portal_v2.ui.lesson_slide_designer import (
    ACTIVITIES, build_presentation_html, new_draft, validate_draft,
)
from portal_v2.ui.workspace_navigation import route_from_label
from scripts.teacher_portal.app import PORTAL_PAGES


def test_designer_route_and_four_activities():
    assert route_from_label("Thiết kế bài giảng").group == "Thiết kế bài học"
    assert "Thiết kế bài giảng" in PORTAL_PAGES
    assert tuple(key for key, _ in ACTIVITIES) == (
        "MO_DAU", "HINH_THANH_KIEN_THUC", "LUYEN_TAP", "VAN_DUNG")


def test_presentation_escapes_teacher_text_and_orders_activities():
    draft = new_draft()
    draft["slides"] = [
        {"id": "2", "activity": "LUYEN_TAP", "title": "Bài tập", "blocks": []},
        {"id": "1", "activity": "MO_DAU", "title": "<script>alert(1)</script>",
         "blocks": [{"kind": "Gợi ý", "text": "1 < 2", "reveal_later": True}]},
    ]
    html = build_presentation_html(draft)
    assert html.index("Mở đầu") < html.index("Luyện tập")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "content fragment" in html


def test_import_rejects_unknown_activity_and_duplicate_slide_ids():
    draft = new_draft()
    slide = {"id": "a", "activity": "MO_DAU", "title": "A", "blocks": []}
    draft["slides"] = [slide, dict(slide)]
    with pytest.raises(ValueError, match="Mã slide"):
        validate_draft(draft)
    draft["slides"] = [dict(slide, activity="UNKNOWN")]
    with pytest.raises(ValueError, match="hoạt động"):
        validate_draft(draft)
