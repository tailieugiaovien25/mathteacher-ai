from datetime import date

import pytest

from educational_planning_v2.models.assignment_round import (
    AssignmentRound,
    AssignmentRoundStatus,
)


def test_assignment_round_builds_default_label():
    item = AssignmentRound(
        round_id="round-1",
        academic_year="2026-2027",
        round_number=1,
        effective_from=date(2026, 8, 24),
    )

    assert item.round_id == "round-1"
    assert item.academic_year == "2026-2027"
    assert item.round_number == 1
    assert item.label == "L\u1ea7n 1"
    assert item.status is AssignmentRoundStatus.ACTIVE


def test_assignment_round_builds_second_round_label():
    item = AssignmentRound(
        round_id="round-2",
        academic_year="2026-2027",
        round_number=2,
        effective_from=date(2026, 10, 1),
    )

    assert item.label == "L\u1ea7n 2"


def test_assignment_round_accepts_custom_label():
    item = AssignmentRound(
        round_id="round-2",
        academic_year="2026-2027",
        round_number=2,
        effective_from=date(2026, 10, 1),
        label="?i?u ch?nh h?c k? I",
    )

    assert item.label == "?i?u ch?nh h?c k? I"


def test_assignment_round_normalizes_text():
    item = AssignmentRound(
        round_id="  round-1  ",
        academic_year="  2026-2027  ",
        round_number=1,
        effective_from=date(2026, 8, 24),
        label="  L?n ??u n?m  ",
    )

    assert item.round_id == "round-1"
    assert item.academic_year == "2026-2027"
    assert item.label == "L?n ??u n?m"


@pytest.mark.parametrize(
    "round_number",
    (
        0,
        -1,
    ),
)
def test_assignment_round_rejects_non_positive_round_number(
    round_number,
):
    with pytest.raises(
        ValueError,
        match="round_number must be at least 1",
    ):
        AssignmentRound(
            round_id="round-x",
            academic_year="2026-2027",
            round_number=round_number,
            effective_from=date(2026, 8, 24),
        )


@pytest.mark.parametrize(
    "round_number",
    (
        "1",
        1.5,
        True,
    ),
)
def test_assignment_round_rejects_invalid_round_number_type(
    round_number,
):
    with pytest.raises(
        TypeError,
        match="round_number must be int",
    ):
        AssignmentRound(
            round_id="round-x",
            academic_year="2026-2027",
            round_number=round_number,
            effective_from=date(2026, 8, 24),
        )


def test_assignment_round_rejects_invalid_status():
    with pytest.raises(
        TypeError,
        match="status must be AssignmentRoundStatus",
    ):
        AssignmentRound(
            round_id="round-1",
            academic_year="2026-2027",
            round_number=1,
            effective_from=date(2026, 8, 24),
            status="ACTIVE",
        )


def test_assignment_round_rejects_invalid_effective_from():
    with pytest.raises(
        TypeError,
        match="effective_from must be a date",
    ):
        AssignmentRound(
            round_id="round-1",
            academic_year="2026-2027",
            round_number=1,
            effective_from="2026-08-24",
        )
