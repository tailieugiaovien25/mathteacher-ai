from portal_v2.context.canonical_code_catalog import CanonicalCodeDefinition
from portal_v2.context.supabase_canonical_code_repository import SupabaseCanonicalCodeRepository

def test_old_constructor_contract_still_works():
    item = CanonicalCodeDefinition("subject", "T", "Toán", True)
    assert item.active is True
    assert item.status == "ACTIVE"
    assert item.rule_version is None

def test_inactive_status_is_derived_from_active():
    item = CanonicalCodeDefinition("component", "TDS", "Đại số", False)
    assert item.status == "INACTIVE"

def test_repository_maps_lifecycle_without_mutating_frozen_object():
    repo = object.__new__(SupabaseCanonicalCodeRepository)
    item = repo._from_row({"namespace":"component","code":"TDS","label":"Đại số","status":"ACTIVE","rule_version":"1","metadata":{"source":"seed"}})
    assert item.status == "ACTIVE"
    assert item.rule_version == "1"
    assert item.metadata == {"source": "seed"}

def test_repository_defaults_missing_optional_lifecycle_fields():
    repo = object.__new__(SupabaseCanonicalCodeRepository)
    item = repo._from_row({"namespace":"subject","code":"T","label":"Toán","status":"ACTIVE"})
    assert item.status == "ACTIVE"
    assert item.rule_version is None
    assert item.metadata == {}
