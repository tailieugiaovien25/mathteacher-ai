from pathlib import Path


def test_active_teaching_session_never_falls_back_to_direct_executor():
    source_path = (
        Path(__file__).resolve().parents[1]
        / "portal_v2"
        / "ui"
        / "teaching_assistant_avatar_surface_streamlit.py"
    )
    source = source_path.read_text(encoding="utf-8")
    start = source.index("if active_session:")
    outer_else = source.index(
        "\n                                else:\n                                    exec_result = executor.execute(action, teacher_confirmed=True)",
        start,
    )
    active_branch = source[start:outer_else]

    assert "teaching_session.execute_plan(" in active_branch
    assert "except Exception as exc:" in active_branch
    assert "executor.execute(action" not in active_branch
    assert "exec_result = None" in source
