import pytest

from educational_planning_v2.models import (
    EducationalPlanAllocationConstraint,
)


def test_allocation_constraint_can_be_created():
    constraint = EducationalPlanAllocationConstraint(
        allocation_key="SH_DS",
        total_periods=67,
    )

    assert constraint.allocation_key == "SH_DS"
    assert constraint.total_periods == 67


def test_allocation_key_is_normalized():
    constraint = EducationalPlanAllocationConstraint(
        allocation_key="  GEOMETRY  ",
        total_periods=33,
    )

    assert constraint.allocation_key == "GEOMETRY"


@pytest.mark.parametrize(
    "allocation_key",
    [
        "",
        "   ",
    ],
)
def test_empty_allocation_key_is_blocked(
    allocation_key,
):
    with pytest.raises(ValueError):
        EducationalPlanAllocationConstraint(
            allocation_key=allocation_key,
            total_periods=10,
        )


def test_total_periods_must_be_int():
    with pytest.raises(TypeError):
        EducationalPlanAllocationConstraint(
            allocation_key="SH_DS",
            total_periods=67.0,
        )


@pytest.mark.parametrize(
    "total_periods",
    [
        0,
        -1,
        -10,
    ],
)
def test_non_positive_total_periods_is_blocked(
    total_periods,
):
    with pytest.raises(ValueError):
        EducationalPlanAllocationConstraint(
            allocation_key="SH_DS",
            total_periods=total_periods,
        )


def test_allocation_constraint_is_immutable():
    constraint = EducationalPlanAllocationConstraint(
        allocation_key="SH_DS",
        total_periods=67,
    )

    with pytest.raises(Exception):
        constraint.total_periods = 68


def test_allocation_constraint_has_no_runtime_responsibility():
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
        EducationalPlanAllocationConstraint.__dict__
    )