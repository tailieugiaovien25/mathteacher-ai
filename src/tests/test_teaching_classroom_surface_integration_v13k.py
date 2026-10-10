from pathlib import Path


def test_lesson_slide_designer_consumes_classroom_runtime_state():
    path = Path(__file__).resolve().parents[1] / "portal_v2" / "ui" / "lesson_slide_designer.py"
    text = path.read_text(encoding="utf-8")
    assert "classroom_runtime_state" in text
    assert "ta_classroom_runtime_state_v13k" in text
    assert "lesson_slide_ids" in text
    assert "lesson_integrated_stages" in text


def test_teacher_assistant_surface_exposes_v13k_controls():
    path = Path(__file__).resolve().parents[1] / "portal_v2" / "ui" / "teaching_assistant_avatar_surface_streamlit.py"
    text = path.read_text(encoding="utf-8")
    for marker in (
        "classroom.stage.show",
        "classroom.whiteboard.show",
        "include_stage",
        "include_whiteboard",
        "V13K",
    ):
        assert marker in text
