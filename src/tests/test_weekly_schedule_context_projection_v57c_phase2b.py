from pathlib import Path

TARGET = (
    Path(__file__).resolve().parents[1]
    / "portal_v2/ui/weekly_schedule_streamlit.py"
)


def source() -> str:
    return TARGET.read_text(encoding="utf-8-sig")


def test_projection_is_shadow_only():
    text = source()
    start = text.index("# V57C_PHASE2_CANONICAL_CONTEXT_PROJECTION")
    end = text.index("    except Exception as error:", start)
    seam = text[start:end]
    assert "# V57C_PHASE2B_SHADOW_ONLY" in seam
    assert "_canonical_projection_snapshot" in seam
    assert "academic_year=authoritative_academic_year" not in seam
    assert "week_number=authoritative_week_number" not in seam


def test_v56_runtime_keeps_existing_selected_year_week_inputs():
    text = source()
    start = text.index("# V57C_PHASE2B_SHADOW_ONLY")
    end = text.index("    except Exception as error:", start)
    seam = text[start:end]
    assert "academic_year=academic_year" in seam
    assert "week_number=int(week_number)" in seam


def test_shadow_projection_has_no_session_state_write():
    text = source()
    start = text.index("# V57C_PHASE2_CANONICAL_CONTEXT_PROJECTION")
    end = text.index("    except Exception as error:", start)
    seam = text[start:end]
    assert "st.session_state[" not in seam
    assert "st.session_state.pop(" not in seam
