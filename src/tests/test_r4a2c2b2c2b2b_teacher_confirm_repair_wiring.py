from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py"


def _wiring_block():
    source = UI.read_text(encoding="utf-8")
    start = source.index("R4A2C2B2C2B2B_ATOMIC_TEACHER_CONFIRM_REPAIR_REAUDIT")
    end = source.index("V14B6F_A8_R2_TEACHER_CONFIRMATION_IS_FINAL", start)
    return source[start:end]


def test_teacher_confirm_repairs_standardized_bytes_then_reaudits_before_commit():
    block = _wiring_block()
    repair = block.index("repair_canonical_field_bytes(")
    reaudit = block.index("audit_repaired_content(")
    commit = block.index("st.session_state[STANDARDIZED_DOCUMENT_KEY] =")
    assert repair < reaudit < commit
    assert "original_content=original_content" in block
    assert "repaired_content=repair_result.content" in block
    assert "repair_source_content" in block


def test_teacher_confirm_invalidates_derived_state_but_preserves_pipeline_evidence():
    block = _wiring_block()
    assert "TEACHER_VERIFICATION_KEY" in block
    assert "AUDIT_RESULT_KEY" in block
    assert "AUDIT_FIELD_EVIDENCE_KEY" in block
    assert "AI_TASK_EVIDENCE_KEY" in block
    assert 'pop("_g1b_v2_pipeline_evidence"' not in block
    assert '"_g1b_v2_pipeline_evidence"' in block


def test_teacher_confirm_commits_rebuilt_audit_and_admin_compliance():
    block = _wiring_block()
    assert "repaired_audit.audit_result" in block
    assert "repaired_audit.canonical_field_rows" in block
    assert "repaired_audit.compliance" in block
    assert "_compliance_monitor_state" in block
    assert '"GATE": "blocked"' in block
    assert '"RELEASE": "blocked"' in block


def test_teacher_confirm_failure_is_atomic_and_fail_closed():
    block = _wiring_block()
    commit = block.index("st.session_state[STANDARDIZED_DOCUMENT_KEY] =")
    error_handler = block.index("except Exception as repair_error:")
    assert commit < error_handler
    error_block = block[error_handler:]
    assert "STANDARDIZED_DOCUMENT_KEY] =" not in error_block
    assert '"level": "error"' in error_block


def test_release_gate_remains_canonical_and_admin():
    source = UI.read_text(encoding="utf-8")
    assert "R4A2C2B2B1_CANONICAL_AND_ADMIN_RELEASE_GATE" in source
    assert "canonical_pass_100\n            and admin_enforcement_pass" in source
