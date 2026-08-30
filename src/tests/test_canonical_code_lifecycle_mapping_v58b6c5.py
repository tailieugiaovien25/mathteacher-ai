from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = (ROOT / "src" / "portal_v2" / "context" / "supabase_canonical_code_repository.py").read_text(encoding="utf-8")

def test_repository_reads_lifecycle_fields():
    assert 'select("namespace,code,label,status,rule_version,metadata")' in REPO

def test_repository_maps_status_rule_version_and_metadata():
    assert '"status": normalized_status' in REPO
    assert '"rule_version":' in REPO
    assert '"metadata": metadata or {}' in REPO
    assert ".update(payload)" in REPO
    assert "setattr(definition" not in REPO

def test_repository_keeps_existing_active_flag_mapping():
    assert 'active=str(row.get("status", "ACTIVE")).upper() == "ACTIVE"' in REPO
