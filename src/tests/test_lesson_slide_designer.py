import pytest

from portal_v2.ui.lesson_slide_designer import (
    ACTIVITIES, activity_overview_html, build_presentation_html, new_draft, tool_workflow, validate_draft,
    save_teacher_draft, list_teacher_drafts, open_teacher_draft,
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


def test_presentation_has_fullscreen_control_separate_from_stage():
    html = build_presentation_html(new_draft())
    assert 'aria-label="Toàn màn hình bài giảng"' in html
    assert 'document.documentElement.requestFullscreen()' in html
    assert 'document.exitFullscreen()' in html
    assert 'Reveal.layout()' in html


def test_designer_overview_keeps_four_saved_activities_and_counts_tools():
    draft = new_draft()
    draft["slides"].append({"activity": "MO_DAU"})
    draft["evidence_cards"].append({"activity": "MO_DAU"})
    html = activity_overview_html(draft)
    assert html.count("<article>") == 4
    assert "Khởi động · ôn bài cũ · 2 nội dung" in html
    assert "Khám phá · làm việc nhóm" in html
    assert "Luyện tập · củng cố" in html
    assert "Vận dụng · tìm tòi mở rộng" in html


def test_tool_workflow_separates_preparation_from_live_operation():
    assert tool_workflow("slide") == "prepare"
    assert tool_workflow("classroom_stage_setup") == "prepare"
    assert tool_workflow("presenter_script") == "prepare"
    assert tool_workflow("stage_play") == "both"
    assert tool_workflow("presenter_speech") == "both"
    assert tool_workflow("evidence_capture") == "both"
    assert tool_workflow("phone_photo_inbox") == "both"


def test_import_rejects_unknown_activity_and_duplicate_slide_ids():
    draft = new_draft()
    slide = {"id": "a", "activity": "MO_DAU", "title": "A", "blocks": []}
    draft["slides"] = [slide, dict(slide)]
    with pytest.raises(ValueError, match="Mã slide"):
        validate_draft(draft)
    draft["slides"] = [dict(slide, activity="UNKNOWN")]
    with pytest.raises(ValueError, match="hoạt động"):
        validate_draft(draft)


def test_owned_draft_roundtrip_uses_scoped_queries():
    class Query:
        def __init__(self, rows): self.rows = rows; self.filters = {}
        def upsert(self, record, *, on_conflict):
            assert on_conflict == "draft_id"
            self.rows[record["draft_id"]] = record
            return self
        def select(self, *_): return self
        def eq(self, field, value): self.filters[field] = value; return self
        def order(self, *_args, **_kwargs): return self
        def limit(self, *_): return self
        def execute(self):
            class Result: pass
            result = Result()
            result.data = [row for row in self.rows.values() if all(
                row.get(field) == value for field, value in self.filters.items())]
            return result
    class Client:
        def __init__(self): self.rows = {}
        def table(self, name):
            assert name == "teacher_lesson_drafts"
            return Query(self.rows)
    client = Client()
    draft = new_draft()
    draft["lesson_title"] = "Bài 1. Tập hợp"
    save_teacher_draft(client, "teacher-A", "draft-A", draft)
    assert len(list_teacher_drafts(client, "teacher-A")) == 1
    assert list_teacher_drafts(client, "teacher-B") == []
    assert open_teacher_draft(client, "teacher-A", "draft-A") == draft
    with pytest.raises(ValueError, match="Không tìm thấy"):
        open_teacher_draft(client, "teacher-B", "draft-A")
