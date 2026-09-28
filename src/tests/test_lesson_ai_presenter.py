import pytest

from portal_v2.ui.lesson_ai_presenter import add_presenter, avatar_data_uri, presenter_speech_script
from portal_v2.ui.lesson_slide_designer import build_presentation_html, new_draft, validate_draft


def test_teacher_authored_role_appears_in_lesson_and_escapes_message():
    draft = new_draft()
    add_presenter(draft, activity="MO_DAU", role="MC", message="Chào lớp! <script>oops()</script>")
    assert validate_draft(draft) is draft
    html = build_presentation_html(draft)
    assert "AI MC" in html
    assert "&lt;script&gt;oops()&lt;/script&gt;" in html
    assert "Chào lớp! <script>" not in html
    assert avatar_data_uri() in html
    assert "data:image/png;base64," in html
    assert 'class="ai-voice-play"' in html
    assert 'class="ai-voice-stop"' in html
    assert 'class="ai-script-line"' in html


def test_speech_only_selects_vietnamese_voice_and_stops_when_slide_changes():
    script = presenter_speech_script()
    assert "vietnameseVoices().find" in script
    assert "^vi(?:-|$)" in script
    assert "utterance.lang='vi-VN'" in script
    assert "Reveal.on('slidechanged',reset)" in script
    assert "synth.speak(utterance)" in script


def test_import_rejects_invalid_role_and_duplicate_id():
    draft = new_draft()
    first = add_presenter(draft, activity="LUYEN_TAP", role="ASSISTANT", message="Em thử trước nhé!")
    draft["ai_presenters"].append(dict(first))
    with pytest.raises(ValueError, match="Mã thẻ"):
        validate_draft(draft)
    draft["ai_presenters"].pop()
    first["role"] = "ADMIN"
    with pytest.raises(ValueError, match="vai trò"):
        validate_draft(draft)
