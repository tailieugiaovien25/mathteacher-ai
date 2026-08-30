from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL = (
    ROOT / "supabase" / "migrations" /
    "202608290003_canonical_code_registry_privileges_v58b6c1.sql"
).read_text(encoding="utf-8").lower()

def test_authenticated_has_minimum_registry_table_privileges():
    assert "grant select, insert, update" in SQL
    assert "on table public.canonical_code_registry" in SQL
    assert "to authenticated" in SQL

def test_delete_is_not_granted():
    assert "revoke delete on table public.canonical_code_registry from authenticated" in SQL
    assert "grant delete" not in SQL

def test_rls_is_not_disabled_or_bypassed():
    assert "disable row level security" not in SQL
    assert "bypassrls" not in SQL
    assert "grant all" not in SQL

def test_anon_has_no_registry_privileges():
    assert "revoke all on table public.canonical_code_registry from anon" in SQL
