from pathlib import Path


TIMETABLE_UI = Path(
    "src/portal_v2/ui/teacher_timetable_streamlit.py"
)


def _source() -> str:
    return TIMETABLE_UI.read_text(
        encoding="utf-8"
    )


def test_teacher_timetable_uses_shared_portal_flash():
    source = _source()

    assert (
        "from portal_v2.ui.portal_flash_feedback import"
        in source
    )

    assert "render_portal_flash(" in source
    assert "set_portal_flash(" in source

    assert (
        "PortalFlashLevel.SUCCESS"
        in source
    )

    assert (
        "PortalFlashLevel.INFO"
        in source
    )


def test_teacher_timetable_renders_flash_after_rerun():
    source = _source()

    render_position = source.find(
        "render_portal_flash("
    )

    save_position = source.rfind(
        "set_portal_flash("
    )

    rerun_position = source.rfind(
        "st.rerun()"
    )

    assert render_position >= 0
    assert save_position >= 0
    assert rerun_position >= 0

    assert render_position < save_position
    assert save_position < rerun_position


def test_teacher_timetable_has_success_feedback():
    source = _source()

    assert (
        '"\\u0110\\u00e3 c\\u1eadp nh\\u1eadt "'
        in source
    )

    assert (
        'f"{changed_count} thay \\u0111\\u1ed5i "'
        in source
    )


def test_teacher_timetable_has_no_change_feedback():
    source = _source()

    assert (
        '"Th\\u1eddi kh\\u00f3a bi\\u1ec3u "'
        in source
    )

    assert (
        '"kh\\u00f4ng c\\u00f3 thay \\u0111\\u1ed5i."'
        in source
    )


def test_teacher_timetable_has_no_private_flash_key():
    source = _source()

    assert (
        "_TIMETABLE_SAVE_FEEDBACK_SESSION_KEY"
        not in source
    )

    assert (
        "teacher_timetable_save_feedback"
        not in source
    )
