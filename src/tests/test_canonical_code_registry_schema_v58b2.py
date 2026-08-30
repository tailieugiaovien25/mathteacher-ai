from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SQL=(ROOT/"supabase/migrations/202608290002_canonical_code_registry_v58b2.sql").read_text(encoding="utf-8")

def test_admin_code_registry_foundation():
    assert "canonical_code_registry" in SQL
    assert "canonical_code_generation_rules" in SQL
    assert "canonical_code_mappings" in SQL
    assert "unique(namespace, code)" in SQL.lower()

def test_teacher_input_has_locked_business_columns():
    for field in ("mon","pmon","ppct","bai","ten_bai","giao_an","ten_tb","sltb"):
        assert field in SQL.lower()
    for field in ("subject_business_id","curriculum_business_id","lesson_plan_business_id","equipment_group_business_id"):
        assert field in SQL.lower()

def test_ppct_provenance_is_structural_not_name_identity():
    low=SQL.lower()
    for field in ("source_version_id","sheet_name","row_position","column_mapping"):
        assert field in low
    assert "unique(owner_user_id, source_version_id, sheet_name, row_position)" in low

def test_initial_rules_match_locked_examples():
    assert "'{grade}{code}'" in SQL
    assert "'{grade}{code}{ppct:03d}'" in SQL
    assert "('lesson_plan','gtds','giáo án toán - đại số')" in SQL.lower()
