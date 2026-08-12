import pytest

import educational_planning_v2.models as planning_models
from educational_planning_v2.models import (
    EducationalPlanAllocationConstraint,
    EducationalPlanAllocationProfile,
)


def _constraint(
    allocation_key: str = "SH_DS",
    total_periods: int = 67,
) -> EducationalPlanAllocationConstraint:
    return EducationalPlanAllocationConstraint(
        allocation_key=allocation_key,
        total_periods=total_periods,
    )


def test_allocation_profile_can_be_created():
    profile = EducationalPlanAllocationProfile(
        profile_id="MATH-G6-2026-2027",
        constraints=(
            _constraint(),
            _constraint("GEOMETRY", 33),
        ),
    )

    assert profile.profile_id == "MATH-G6-2026-2027"
    assert profile.constraints == (
        _constraint(),
        _constraint("GEOMETRY", 33),
    )


def test_profile_id_is_normalized():
    profile = EducationalPlanAllocationProfile(
        profile_id="  MATH-G6-2026-2027  ",
        constraints=(_constraint(),),
    )

    assert profile.profile_id == "MATH-G6-2026-2027"


@pytest.mark.parametrize(
    "profile_id",
    [
        "",
        "   ",
    ],
)
def test_empty_profile_id_is_blocked(profile_id):
    with pytest.raises(ValueError):
        EducationalPlanAllocationProfile(
            profile_id=profile_id,
            constraints=(_constraint(),),
        )


def test_constraints_must_be_tuple():
    with pytest.raises(TypeError):
        EducationalPlanAllocationProfile(
            profile_id="MATH-G6-2026-2027",
            constraints=[_constraint()],
        )


def test_constraints_must_not_be_empty():
    with pytest.raises(ValueError):
        EducationalPlanAllocationProfile(
            profile_id="MATH-G6-2026-2027",
            constraints=(),
        )


def test_every_constraint_must_be_allocation_constraint():
    with pytest.raises(TypeError):
        EducationalPlanAllocationProfile(
            profile_id="MATH-G6-2026-2027",
            constraints=("not-a-constraint",),
        )


def test_duplicate_allocation_key_is_blocked():
    with pytest.raises(ValueError):
        EducationalPlanAllocationProfile(
            profile_id="MATH-G6-2026-2027",
            constraints=(
                _constraint("SH_DS", 67),
                _constraint("SH_DS", 68),
            ),
        )


def test_allocation_profile_is_immutable():
    profile = EducationalPlanAllocationProfile(
        profile_id="MATH-G6-2026-2027",
        constraints=(_constraint(),),
    )

    with pytest.raises(Exception):
        profile.profile_id = "OTHER"


def test_allocation_profile_has_no_runtime_responsibility():
    forbidden = {
        "allocate",
        "validate",
        "build",
        "execute",
        "route",
        "render",
        "export",
    }

    assert forbidden.isdisjoint(
        EducationalPlanAllocationProfile.__dict__
    )


def test_allocation_contracts_are_public_model_exports():
    assert (
        "EducationalPlanAllocationConstraint"
        in planning_models.__all__
    )
    assert (
        "EducationalPlanAllocationProfile"
        in planning_models.__all__
    )