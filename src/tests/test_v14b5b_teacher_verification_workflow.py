from pathlib import Path
P=Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")
def src(): return P.read_text(encoding="utf-8")
def test_teacher_verification_audit_trail():
 s=src()
 assert 'TEACHER_VERIFICATION_KEY = "g1b_v2_teacher_canonical_verification"' in s
 assert '"teacher_value"' in s
 assert '"verified_by": str(user_id or "")' in s
 assert '"verified_at": datetime.now(timezone.utc).isoformat()' in s
def test_confirmation_bound_to_artifact_and_evidence():
 s=src()
 assert 'sha256(standardized_snapshot_content).hexdigest()' in s
 assert 'str(_verified.get("output_sha256") or "") == verification_scope["output_sha256"]' in s
 assert 'str(_verified.get("expected_snapshot") or "") == str(_row.get("expected") or "")' in s
 assert 'str(_verified.get("found_snapshot") or "") == str(_row.get("found") or "")' in s
def test_stale_clear():
 s=src(); i=s.index("# V14B3_CLEAR_STALE_CANONICAL_EVIDENCE")
 assert "st.session_state.pop(TEACHER_VERIFICATION_KEY, None)" in s[i:i+700]
def test_five_fields_and_admin_both_required():
 s=src()
 assert 'canonical_pass_100 = bool(canonical_field_rows) and all(' in s
 assert '("accepted", "teacher_verified")' in s
 assert 'admin_enforcement_pass = (' in s
 assert 'release_allowed = canonical_pass_100' in s
 assert 'audit_blocks_save = not release_allowed' in s
def test_explicit_teacher_action():
 s=src()
 assert "st.text_input(" in s
 assert "X\\u00e1c nh\\u1eadn l\\u00e0 \\u0111\\u00fang" in s
 assert "No revoke control: teacher confirmation is final business verification." in s
def test_management_gate_preserved():
 s=src()
 assert "if standardized_content:\n        if not audit_blocks_save:" in s
