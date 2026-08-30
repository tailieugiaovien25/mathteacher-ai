from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def _repo_text():
    return (ROOT / "src/lesson_planning_v2/adapters/supabase_lesson_plan_configuration_repository.py").read_text(encoding="utf-8")

def _migration_text():
    return (ROOT / "supabase/migrations/202608300012_admin_lesson_plan_configuration_foundation_v58c6a4.sql").read_text(encoding="utf-8")

def test_profile_primary_key_matches_migration_0012():
    repo = _repo_text()
    migration = _migration_text()
    assert "profile_id uuid primary key" in migration
    assert "configuration_profile_id" not in migration
    assert "configuration_profile_id" not in repo
    assert '"profile_id,profile_code,profile_name,"' in repo

def test_version_profile_foreign_key_matches_migration_0012():
    repo = _repo_text()
    migration = _migration_text()
    assert "profile_id uuid not null" in migration
    assert "references public.lesson_plan_configuration_profiles(profile_id)" in migration
    assert '"configuration_version_id,profile_id,"' in repo
    assert 'version.get("profile_id")' in repo
    assert 'profile.get("profile_id")' in repo

def test_version_primary_key_remains_configuration_version_id():
    repo = _repo_text()
    migration = _migration_text()
    assert "configuration_version_id uuid primary key" in migration
    assert '.eq("configuration_version_id", configuration_version_id)' in repo

def test_snapshot_uses_real_profile_id_column():
    repo = _repo_text()
    assert 'profile_id=str(profile.get("profile_id") or "")' in repo
