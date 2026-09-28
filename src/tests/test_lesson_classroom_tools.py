import pytest

from portal_v2.ui.lesson_classroom_tools import add_tool, build_owned_stage
from portal_v2.ui.lesson_slide_designer import build_presentation_html, new_draft, validate_draft


def test_classroom_stage_cards_are_portable_and_import_checked():
    draft = new_draft()
    tool = add_tool(draft, activity="MO_DAU", kind="LUCKY_WHEEL",
                    session_id="owned-session", title="Ôn tập đầu giờ")
    assert validate_draft(draft) is draft
    assert "Vòng quay may mắn" in build_presentation_html(draft)
    draft["classroom_tools"].append(dict(tool))
    with pytest.raises(ValueError, match="Mã thẻ"):
        validate_draft(draft)


def test_prepared_stage_is_embedded_in_activity_slide():
    draft = new_draft()
    tool = add_tool(draft, activity="LUYEN_TAP", kind="QUESTION_STAGE",
                    session_id="owned-session", title="Bộ câu luyện tập")
    stage = b'<!doctype html><html><body><button>Next &amp; check</button></body></html>'
    html = build_presentation_html(draft, classroom_stages={tool["id"]: stage})
    assert 'srcdoc="&lt;!doctype html&gt;' in html
    assert 'Next &amp;amp; check' in html
    assert 'class="classroom-stage-shell"' in html
    assert '⛶ Toàn màn hình' in html
    assert 'shell.requestFullscreen()' in html
    assert '.classroom-stage-shell:fullscreen{width:100vw;height:100vh' in html
    assert 'Chuẩn bị sân khấu tích hợp để trình chiếu' not in html
    assert html.index('3 · Luyện tập') < html.index('srcdoc=')


def test_imported_session_cannot_be_launched_without_ownership():
    class Query:
        def select(self, *_): return self
        def eq(self, *_): return self
        def limit(self, *_): return self
        def execute(self): return type("Result", (), {"data": []})()

    class Client:
        def table(self, name):
            assert name == "teacher_classroom_sessions"
            return Query()

    draft = new_draft()
    tool = add_tool(draft, activity="MO_DAU", kind="GAMESHOW",
                    session_id="another-teacher-session", title="Game")
    with pytest.raises(ValueError, match="không còn thuộc tài khoản"):
        build_owned_stage(Client(), "current-teacher", tool)
