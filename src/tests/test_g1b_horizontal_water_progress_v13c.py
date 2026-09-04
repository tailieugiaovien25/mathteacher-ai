from pathlib import Path


UI = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")


def test_monitor_is_long_thin_horizontal_strip_below_action_row():
    text = UI.read_text(encoding="utf-8")
    assert "task_monitor_slot = actions[0].empty()" in text
    assert "width:calc(300% + 2rem)" in text
    assert "height:132px" in text
    assert "overflow-y:hidden" in text
    assert 'class="g1b-task-flow"' in text
    assert "grid-template-columns:repeat(11" in text


def test_only_running_real_task_uses_water_flow_animation():
    text = UI.read_text(encoding="utf-8")
    assert ".g1b-running{" in text
    assert "background-size:260% 100%" in text
    assert "animation:g1bwater 1.25s linear infinite" in text
    assert "@keyframes g1bwater" in text
    assert "_apply_real_progress_event" in text
    assert 'handler_arguments["progress_callback"]' in text


def test_status_colors_remain_distinct_and_gate_is_retained():
    text = UI.read_text(encoding="utf-8")
    assert ".g1b-pass{" in text
    assert ".g1b-blocked{" in text
    assert ".g1b-review,.g1b-unverified{" in text
    assert "release_allowed = canonical_pass_100" in text
    assert "audit_blocks_save = not release_allowed" in text


def test_non_compliant_conclusions_have_diagonal_end_marker():
    text = UI.read_text(encoding="utf-8")
    assert ".g1b-blocked::after,.g1b-review::after,.g1b-unverified::after" in text
    assert "transform:rotate(34deg)" in text
    assert ".g1b-blocked::after{background:#d93636}" in text
    assert ".g1b-review::after{background:#d49a00}" in text
    assert ".g1b-unverified::after{background:#8090a4}" in text
    assert ".g1b-pass::after" not in text
    assert ".g1b-running::after" not in text
