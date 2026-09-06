from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = (
    ROOT
    / "src"
    / "portal_v2"
    / "ui"
    / "admin_subject_coordination_workspace_streamlit.py"
)


def test_effective_lesson_plan_details_receives_defined_payload():
    text = TARGET.read_text(encoding="utf-8-sig")

    bad = (
        "_g1b_p1b_r2a_render_effective_lesson_plan_details"
        "(st, configuration_payload)"
    )
    good = (
        "_g1b_p1b_r2a_render_effective_lesson_plan_details"
        "(st, payload)"
    )

    assert bad not in text
    assert good in text
    assert 'payload = getattr(value, "configuration_payload", {}) or {}' in text


def test_effective_details_contract_accepts_payload():
    text = TARGET.read_text(encoding="utf-8-sig")

    assert (
        "def _g1b_p1b_r2a_render_effective_lesson_plan_details"
        "(st, payload) -> None:"
    ) in text
    assert "normalized = dict(payload or {})" in text
