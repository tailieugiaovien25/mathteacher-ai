from datetime import date

import pytest

from educational_planning_v2.adapters.academic_week_payload_adapter import (
    AcademicWeekPayloadAdapter,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
    OperationalPayloadReference,
)


def make_envelope(payload):
    return OperationalPayloadEnvelope(
        reference=OperationalPayloadReference(
            source_id="academic-week-2026-2027",
            data_type=OperationalDataType.ACADEMIC_WEEK,
            payload_version="v1",
        ),
        payload=payload,
    )


def test_parses_academic_week_payload():
    adapter = AcademicWeekPayloadAdapter()

    weeks = adapter.parse(
        envelope=make_envelope(
            (
                {
                    "academic_year": "2026-2027",
                    "week_number": 1,
                    "start_date": "2026-09-07",
                    "end_date": "2026-09-13",
                },
                {
                    "academic_year": "2026-2027",
                    "week_number": 2,
                    "start_date": "2026-09-14",
                    "end_date": "2026-09-20",
                },
            )
        )
    )

    assert len(weeks) == 2
    assert weeks[0].academic_year == "2026-2027"
    assert weeks[0].week_number == 1
    assert weeks[0].start_date == date(2026, 9, 7)
    assert weeks[0].end_date == date(2026, 9, 13)


def test_accepts_date_objects():
    adapter = AcademicWeekPayloadAdapter()

    weeks = adapter.parse(
        envelope=make_envelope(
            (
                {
                    "academic_year": "2026-2027",
                    "week_number": 1,
                    "start_date": date(2026, 9, 7),
                    "end_date": date(2026, 9, 13),
                },
            )
        )
    )

    assert weeks[0].start_date == date(2026, 9, 7)
    assert weeks[0].end_date == date(2026, 9, 13)


def test_find_week_returns_requested_week():
    adapter = AcademicWeekPayloadAdapter()

    envelope = make_envelope(
        (
            {
                "academic_year": "2026-2027",
                "week_number": 1,
                "start_date": "2026-09-07",
                "end_date": "2026-09-13",
            },
            {
                "academic_year": "2026-2027",
                "week_number": 2,
                "start_date": "2026-09-14",
                "end_date": "2026-09-20",
            },
        )
    )

    week = adapter.find_week(
        envelope=envelope,
        academic_year="2026-2027",
        week_number=2,
    )

    assert week.week_number == 2
    assert week.start_date == date(2026, 9, 14)


def test_duplicate_academic_week_is_rejected():
    adapter = AcademicWeekPayloadAdapter()

    envelope = make_envelope(
        (
            {
                "academic_year": "2026-2027",
                "week_number": 1,
                "start_date": "2026-09-07",
                "end_date": "2026-09-13",
            },
            {
                "academic_year": "2026-2027",
                "week_number": 1,
                "start_date": "2026-09-07",
                "end_date": "2026-09-13",
            },
        )
    )

    with pytest.raises(
        ValueError,
        match="duplicate academic week",
    ):
        adapter.parse(
            envelope=envelope
        )


def test_missing_week_is_rejected():
    adapter = AcademicWeekPayloadAdapter()

    envelope = make_envelope(
        (
            {
                "academic_year": "2026-2027",
                "week_number": 1,
                "start_date": "2026-09-07",
                "end_date": "2026-09-13",
            },
        )
    )

    with pytest.raises(
        LookupError,
        match="academic week not found",
    ):
        adapter.find_week(
            envelope=envelope,
            academic_year="2026-2027",
            week_number=9,
        )


def test_wrong_operational_data_type_is_rejected():
    adapter = AcademicWeekPayloadAdapter()

    envelope = OperationalPayloadEnvelope(
        reference=OperationalPayloadReference(
            source_id="ppct-1",
            data_type=OperationalDataType.PPCT,
            payload_version="v1",
        ),
        payload=(),
    )

    with pytest.raises(
        ValueError,
        match="ACADEMIC_WEEK",
    ):
        adapter.parse(
            envelope=envelope
        )


def test_invalid_iso_date_is_rejected():
    adapter = AcademicWeekPayloadAdapter()

    envelope = make_envelope(
        (
            {
                "academic_year": "2026-2027",
                "week_number": 1,
                "start_date": "not-a-date",
                "end_date": "2026-09-13",
            },
        )
    )

    with pytest.raises(
        ValueError,
        match="start_date must be ISO date",
    ):
        adapter.parse(
            envelope=envelope
        )
