from pathlib import Path


UI = Path(
    "src/portal_v2/ui/"
    "lesson_plan_template_setup_streamlit.py"
)

APP = Path(
    "scripts/teacher_portal/app.py"
)


def ui_source():
    return UI.read_text(
        encoding="utf-8-sig"
    )


def app_source():
    return APP.read_text(
        encoding="utf-8"
    )


def test_uses_teacher_subject_service():
    text = ui_source()

    assert (
        "TeacherLessonPlanSubjectService"
        in text
    )

    assert (
        "SupabaseTeacherSubjectAssignmentRepository"
        in text
    )

    assert (
        "SupabaseSubjectCatalogRepository"
        in text
    )


def test_render_accepts_authenticated_context():
    text = ui_source()

    assert (
        "client=None"
        in text
    )

    assert (
        "teacher_id: str | None"
        in text
    )

    assert (
        "academic_year: str | None"
        in text
    )


def test_subject_is_selected_by_canonical_id():
    text = ui_source()

    assert (
        "selected_subject_id"
        in text
    )

    assert (
        "subject_by_id"
        in text
    )

    assert (
        '"lesson_plan_template_subject"'
        in text
    )


def test_profile_session_is_teacher_year_subject_scoped():
    text = ui_source()

    assert (
        "def _context_session_key("
        in text
    )

    assert (
        "teacher_id"
        in text
    )

    assert (
        "academic_year"
        in text
    )

    assert (
        "subject_id"
        in text
    )


def test_subject_profile_is_separate():
    text = ui_source()

    assert (
        "SubjectLessonPlanProfile"
        in text
    )

    assert (
        "subject_profile_session_key"
        in text
    )


def test_flexible_modes_are_configured_per_subject():
    text = ui_source()

    assert (
        "LessonPlanSelectionMode.LESSON"
        in text
    )

    assert (
        "LessonPlanSelectionMode.PERIOD"
        in text
    )

    assert (
        "LessonPlanSelectionMode.TOPIC"
        in text
    )

    assert (
        "allowed_selection_modes"
        in text
    )

    assert (
        "default_selection_mode"
        in text
    )


def test_save_is_not_global_session_profile():
    text = ui_source()

    assert (
        "st.session_state[\n"
        "            profile_session_key\n"
        "        ] = candidate"
        in text
    )

    assert (
        "SESSION_KEY\n"
        not in text
    )


def test_portal_passes_authenticated_context():
    text = app_source()

    assert (
        "render_lesson_plan_template_setup("
        in text
    )

    assert "client=client" in text

    assert (
        "teacher_id=str(user_id)"
        in text
    )
