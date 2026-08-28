from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MIGRATION=ROOT/"supabase/migrations/202608280004_canonical_competency_foundation.sql"

def test_competency_migration_integrates_existing_backbone():
    text=MIGRATION.read_text(encoding="utf-8")
    for table in ("competency_frameworks","competency_components","competency_indicators","competency_grade_descriptors","competency_descriptor_constraints","competency_requirement_links","competency_aliases","competency_projection_mappings","competency_crosswalks","competency_audit_log"):
        assert f"public.{table}" in text
    assert "references public.subjects(subject_id)" in text
    assert "references public.grades(grade_id)" in text
    assert "references public.assessment_learning_requirements(requirement_code)" in text
    assert "assessment_mathematical_competencies" in text

def test_competency_seed_has_all_five_frameworks_and_155_indicators():
    text=MIGRATION.read_text(encoding="utf-8")
    for code in ("'NLC'","'MATH'","'ENG'","'DIG'","'AI'"):
        assert code in text
    assert text.count("insert into public.competency_indicators(") == 155
    assert text.count("insert into public.competency_grade_descriptors(") == 80

def test_admin_governance_is_rls_audited_and_non_destructive():
    text=MIGRATION.read_text(encoding="utf-8")
    assert "competency_admin_authorized" in text
    assert "competency_audit_log" in text
    assert "DEPRECATED" in text
    assert "replaced_by_indicator_id" in text
    assert "grant select,insert,update,delete" not in text
    assert "admin_delete" not in text
