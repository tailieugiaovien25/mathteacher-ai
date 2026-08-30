from pathlib import Path


APP = Path(
    "scripts/teacher_portal/app.py"
)


def source():
    return APP.read_text(
        encoding="utf-8-sig"
    )


def test_teacher_portal_exposes_lesson_plan_template_page():
    text = source()

    assert "lesson_plan_template_setup_streamlit" not in text
    assert "render_lesson_plan_template_setup" not in text


def test_teacher_portal_unifies_profile_assignment_and_template_settings():
    text = source()

    assert "Thiết đặt giáo viên" in text
    assert "def render_teacher_settings(" in text
    assert "lesson_plan_template_setup_streamlit" not in text
    assert "render_lesson_plan_template_setup" not in text
