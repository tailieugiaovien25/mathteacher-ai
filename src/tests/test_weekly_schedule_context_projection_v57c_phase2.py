from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "portal_v2/ui/weekly_schedule_streamlit.py"

def source():
    return TARGET.read_text(encoding="utf-8-sig")

def test_adapter_imported():
    text = source()
    assert "from portal_v2.context.legacy_session_context_adapter import (" in text
    assert "project_system_context," in text

def test_projection_precedes_v56_authority_call():
    text = source()
    start = text.index("# V57C_PHASE2_CANONICAL_CONTEXT_PROJECTION")
    projection = text.index("canonical_context = project_system_context(", start)
    runtime = text.index("view = _build_standardization_authoritative_week_view(", start)
    assert start < projection < runtime

def test_projection_seam_has_no_session_write():
    text = source()
    start = text.index("# V57C_PHASE2_CANONICAL_CONTEXT_PROJECTION")
    end = text.index("    except Exception as error:", start)
    seam = text[start:end]
    assert "st.session_state[" not in seam
    assert "st.session_state.pop(" not in seam
    assert "_canonical_projection_snapshot" in seam
    assert "academic_year=academic_year" in seam
    assert "week_number=int(week_number)" in seam
    assert "_build_standardization_authoritative_week_view(" in seam
