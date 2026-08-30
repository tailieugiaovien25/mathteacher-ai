from portal_v2.context.ownership import (
    ContextStateRole,
    build_default_context_ownership_registry,
)


def test_default_ownership_registry_has_no_competing_canonical_owners():
    registry = build_default_context_ownership_registry()
    assert registry.competing_owners() == ()


def test_week_has_one_canonical_owner_and_legacy_widget_aliases():
    registry = build_default_context_ownership_registry()
    aliases = registry.aliases_for("week_number")
    canonical = [x for x in aliases if x.role == ContextStateRole.CANONICAL]
    assert [x.state_key for x in canonical] == ["global_weekly_active_week_number"]
    assert registry.get("standardization_authoring_week_number").role == ContextStateRole.WIDGET
    assert registry.get("system_weekly_week_number").role == ContextStateRole.LEGACY_ALIAS


def test_standardization_subject_component_are_widget_inputs_not_authority():
    registry = build_default_context_ownership_registry()
    assert registry.get("standardization_subject_filter").role == ContextStateRole.WIDGET
    assert registry.get("standardization_component_filter").role == ContextStateRole.WIDGET
    assert registry.get("standardization_subject_filter").authority == "TEACHING_ASSIGNMENT"


def test_portal_navigation_widget_ownership_is_explicit():
    registry = build_default_context_ownership_registry()
    item = registry.get("portal_navigation")
    assert item.role == ContextStateRole.WIDGET
    assert item.owner == "STREAMLIT_WIDGET"
    assert item.canonical_field is None
