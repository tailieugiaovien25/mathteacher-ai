from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SQL=(ROOT/"supabase/migrations/202608290002_canonical_code_registry_v58b2.sql").read_text(encoding="utf-8").lower()

def test_uses_existing_portal_roles_admin_authority():
    assert "from public.portal_roles pr" in SQL
    assert "pr.user_id = (select auth.uid())" in SQL
    assert "pr.role = 'admin'" in SQL

def test_does_not_invent_admin_function():
    assert "is_portal_admin()" not in SQL

def test_registry_rule_mapping_mutations_are_admin_guarded():
    for policy in (
        "canonical_code_registry_admin_write",
        "canonical_code_rules_admin_write",
        "canonical_code_mappings_admin_write",
    ):
        pos=SQL.index(policy)
        window=SQL[pos:pos+1800]
        assert "from public.portal_roles pr" in window
        assert "pr.role = 'admin'" in window

def test_teacher_input_owner_or_admin_contract():
    pos=SQL.index("canonical_teacher_input_owner_read")
    window=SQL[pos:pos+1600]
    assert "owner_user_id = (select auth.uid())" in window
    assert "from public.portal_roles pr" in window
    assert "pr.role = 'admin'" in window
