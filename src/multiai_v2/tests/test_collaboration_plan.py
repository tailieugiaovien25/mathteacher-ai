import pytest

from src.multiai_v2.contracts import (
    CollaborationPlan,
    CollaborationRole,
)


def _role(
    role_id: str = "proposer",
    capability_id: str = "lesson.pedagogical_proposal",
) -> CollaborationRole:
    return CollaborationRole(
        role_id=role_id,
        capability_id=capability_id,
        capability_version="1.0",
    )


def test_collaboration_plan_can_be_created():
    roles = (
        _role(),
        _role(
            role_id="verifier",
            capability_id="lesson.pedagogical_review",
        ),
    )

    plan = CollaborationPlan(
        collaboration_id="lesson-design",
        roles=roles,
    )

    assert plan.collaboration_id == "lesson-design"
    assert plan.roles == roles


def test_collaboration_plan_normalizes_collaboration_id():
    plan = CollaborationPlan(
        collaboration_id="  lesson-design  ",
        roles=(_role(),),
    )

    assert plan.collaboration_id == "lesson-design"


@pytest.mark.parametrize(
    "collaboration_id",
    [
        "",
        "   ",
    ],
)
def test_empty_collaboration_id_is_blocked(
    collaboration_id,
):
    with pytest.raises(ValueError):
        CollaborationPlan(
            collaboration_id=collaboration_id,
            roles=(_role(),),
        )


def test_empty_roles_are_blocked():
    with pytest.raises(ValueError):
        CollaborationPlan(
            collaboration_id="lesson-design",
            roles=(),
        )


def test_roles_must_be_tuple():
    with pytest.raises(TypeError):
        CollaborationPlan(
            collaboration_id="lesson-design",
            roles=[_role()],
        )


def test_every_role_must_be_collaboration_role():
    with pytest.raises(TypeError):
        CollaborationPlan(
            collaboration_id="lesson-design",
            roles=(
                _role(),
                "not-a-role",
            ),
        )


def test_duplicate_role_ids_are_blocked():
    with pytest.raises(ValueError):
        CollaborationPlan(
            collaboration_id="lesson-design",
            roles=(
                _role(
                    role_id="verifier",
                    capability_id="lesson.review.a",
                ),
                _role(
                    role_id="verifier",
                    capability_id="lesson.review.b",
                ),
            ),
        )


def test_same_capability_can_be_used_by_different_roles():
    plan = CollaborationPlan(
        collaboration_id="lesson-design",
        roles=(
            _role(role_id="reviewer-a"),
            _role(role_id="reviewer-b"),
        ),
    )

    assert len(plan.roles) == 2


def test_collaboration_plan_is_immutable():
    plan = CollaborationPlan(
        collaboration_id="lesson-design",
        roles=(_role(),),
    )

    with pytest.raises(Exception):
        plan.collaboration_id = "changed"


def test_collaboration_plan_has_no_provider_or_execution_responsibility():
    forbidden = {
        "provider_id",
        "execute",
        "select",
        "route",
        "fallback",
        "validate",
        "accept",
        "reject",
        "register",
    }

    assert forbidden.isdisjoint(
        CollaborationPlan.__dict__
    )