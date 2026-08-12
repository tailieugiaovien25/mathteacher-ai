import pytest

from src.multiai_v2.contracts import CollaborationRole


def test_collaboration_role_can_be_created():
    role = CollaborationRole(
        role_id="proposer",
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
    )

    assert role.role_id == "proposer"
    assert (
        role.capability_id
        == "lesson.pedagogical_proposal"
    )
    assert role.capability_version == "1.0"


def test_collaboration_role_normalizes_identity_fields():
    role = CollaborationRole(
        role_id="  verifier  ",
        capability_id="  lesson.pedagogical_review  ",
        capability_version="  1.0  ",
    )

    assert role.role_id == "verifier"
    assert (
        role.capability_id
        == "lesson.pedagogical_review"
    )
    assert role.capability_version == "1.0"


@pytest.mark.parametrize(
    "role_id",
    [
        "",
        "   ",
    ],
)
def test_empty_role_id_is_blocked(role_id):
    with pytest.raises(ValueError):
        CollaborationRole(
            role_id=role_id,
            capability_id="lesson.pedagogical_proposal",
            capability_version="1.0",
        )


@pytest.mark.parametrize(
    "capability_id",
    [
        "",
        "   ",
    ],
)
def test_empty_capability_id_is_blocked(
    capability_id,
):
    with pytest.raises(ValueError):
        CollaborationRole(
            role_id="proposer",
            capability_id=capability_id,
            capability_version="1.0",
        )


@pytest.mark.parametrize(
    "capability_version",
    [
        "",
        "   ",
    ],
)
def test_empty_capability_version_is_blocked(
    capability_version,
):
    with pytest.raises(ValueError):
        CollaborationRole(
            role_id="proposer",
            capability_id="lesson.pedagogical_proposal",
            capability_version=capability_version,
        )


def test_collaboration_role_is_immutable():
    role = CollaborationRole(
        role_id="proposer",
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
    )

    with pytest.raises(Exception):
        role.role_id = "verifier"


def test_collaboration_role_has_no_execution_or_acceptance_responsibility():
    forbidden = {
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
        CollaborationRole.__dict__
    )