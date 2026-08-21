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

    assert (
        "lesson_plan_template_setup_streamlit"
        in text
    )

    assert (
        "render_lesson_plan_template_setup"
        in text
    )

    assert (
        "Mẫu giáo án"
        in text
    )
