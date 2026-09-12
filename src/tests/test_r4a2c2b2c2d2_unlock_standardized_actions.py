from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

TARGET = (
    ROOT
    / "src"
    / "portal_v2"
    / "ui"
    / "standardized_lesson_plan_authoring_v2_streamlit.py"
)


def source():
    return TARGET.read_text(encoding="utf-8")


def management_block():
    value = source()

    start = value.index(
        "R4A2C2B2C2D2_MANAGEMENT_MERGE_NOT_BLOCKED_BY_AUDIT"
    )

    end = value.index(
        "G1B_13H1R4B4J_SAVE_AND_BACK_NAV",
        start,
    )

    return value[start:end]


def test_save_remains_available_when_audit_blocks():
    value = source()

    assert (
        "disabled=(save_handler is None or not standardized_content),"
        in value
    )

    assert (
        "disabled=(save_handler is None or not standardized_content or audit_blocks_save),"
        not in value
    )


def test_download_remains_available_when_audit_blocks():
    value = source()

    assert "disabled=(not standardized_content)," in value

    assert (
        "disabled=(not standardized_content or audit_blocks_save),"
        not in value
    )


def test_management_workspace_is_always_rendered_for_standardized_docx():
    block = management_block()

    assert "if standardized_content:" in block

    assert (
        "render_standardized_lesson_plan_management("
        in block
    )

    assert "save_handler=save_handler," in block

    assert "if not audit_blocks_save:" not in block


def test_management_save_handler_is_not_removed_by_audit():
    block = management_block()

    assert (
        "save_handler=save_handler if not audit_blocks_save else None"
        not in block
    )


def test_audit_remains_present_as_supervisory_signal():
    value = source()

    assert "audit_blocks_save = not release_allowed" in value
    assert "canonical_pass_100" in value
    assert "admin_enforcement_pass" in value

    block = management_block()

    assert "if audit_blocks_save:" in block
    assert "st.warning(" in block
