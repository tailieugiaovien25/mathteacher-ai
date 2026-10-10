from ai_kernel import AIAdminControl, AIActionClass, AISkillSpec, AISkillDomain


def test_admin_skill_registry_has_standardization_and_marketing_locked():
    control = AIAdminControl()
    ids = {item.skill_id for item in control.skills}
    assert "document.standardization.audit" in ids
    marketing = next(item for item in control.skills if item.skill_id == "marketing.assistant")
    assert marketing.admin_enabled is False


def test_standardization_skill_is_advisory_only():
    control = AIAdminControl()
    skill = control.resolve_skill("document.standardization.audit")
    assert AIActionClass.ADVISORY in skill.allowed_actions
    assert AIActionClass.MUTATING not in skill.allowed_actions


def test_unknown_or_disabled_skill_is_not_resolved():
    control = AIAdminControl()
    try:
        control.resolve_skill("marketing.assistant")
    except RuntimeError as exc:
        assert "chưa bật" in str(exc)
    else:
        raise AssertionError("disabled skill must not resolve")
