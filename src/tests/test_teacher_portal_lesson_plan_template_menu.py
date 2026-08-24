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


def test_teacher_portal_unifies_profile_assignment_and_template_settings():
    text = source()

    assert "Thiết đặt giáo viên" in text
    assert "def render_teacher_settings(" in text
    assert '"1. Thông tin giáo viên"' in text
    assert '"2. Phân công và nhiệm vụ"' in text
    assert '"3. Thiết đặt giáo án (Mẫu giáo án)"' in text
    assert "SupabaseTeachingAssignmentRepository(" in text
    assert "SupabaseClassCatalogRepository(" in text
    assert "SupabaseSubjectCatalogRepository(" in text
    assert "render_lesson_plan_template_setup(" in text
    assert "embedded=True" in text
    assert 'elif selected == "Thiết đặt giáo viên":' in text
    assert "'H\\u1ed3 s\\u01a1 gi\\xe1o vi\\xean'," not in text
