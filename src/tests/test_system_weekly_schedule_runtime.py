import pytest

from portal_v2.runtime.system_weekly_schedule_runtime import (
    SystemWeeklyScheduleRuntime,
    SystemWeeklyScheduleRuntimeRequest,
)


def test_runtime_requires_client():
    with pytest.raises(
        ValueError,
        match="client must not be None",
    ):
        SystemWeeklyScheduleRuntime(
            client=None,
            user_id="teacher-1",
        )


def test_runtime_requires_user_id():
    with pytest.raises(
        ValueError,
        match="user_id must not be empty",
    ):
        SystemWeeklyScheduleRuntime(
            client=object(),
            user_id="   ",
        )


def test_runtime_request_contract():
    request = (
        SystemWeeklyScheduleRuntimeRequest(
            schedule_id="schedule-1",
            academic_year="2026-2027",
            week_number=5,
            ppct_scope_rules=(),
        )
    )

    assert request.schedule_id == "schedule-1"
    assert request.academic_year == "2026-2027"
    assert request.week_number == 5
    assert request.ppct_scope_rules == ()
