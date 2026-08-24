from datetime import date
from types import SimpleNamespace

import pytest

from educational_planning_v2.adapters.supabase_assignment_round_repository import (
    SupabaseAssignmentRoundRepository,
)
from educational_planning_v2.models.assignment_round import (
    AssignmentRound,
    AssignmentRoundStatus,
)


class FakeQuery:
    def __init__(
        self,
        rows=None,
    ):
        self.rows = [] if rows is None else rows
        self.calls = []

    def select(
        self,
        value,
    ):
        self.calls.append(
            ("select", value)
        )
        return self

    def upsert(
        self,
        row,
        on_conflict=None,
    ):
        self.calls.append(
            (
                "upsert",
                row,
                on_conflict,
            )
        )
        self.rows = [row]
        return self

    def eq(
        self,
        field,
        value,
    ):
        self.calls.append(
            ("eq", field, value)
        )
        return self

    def limit(
        self,
        value,
    ):
        self.calls.append(
            ("limit", value)
        )
        return self

    def order(
        self,
        value,
    ):
        self.calls.append(
            ("order", value)
        )
        return self

    def delete(
        self,
    ):
        self.calls.append(
            ("delete",)
        )
        return self

    def execute(
        self,
    ):
        return SimpleNamespace(
            data=self.rows
        )


class FakeClient:
    def __init__(
        self,
        rows=None,
    ):
        self.query = FakeQuery(
            rows=rows
        )
        self.table_names = []

    def table(
        self,
        table_name,
    ):
        self.table_names.append(
            table_name
        )
        return self.query


def test_repository_requires_client():
    with pytest.raises(
        ValueError,
        match="client must not be None",
    ):
        SupabaseAssignmentRoundRepository(
            client=None
        )


def test_save_round():
    client = FakeClient()

    repository = (
        SupabaseAssignmentRoundRepository(
            client=client
        )
    )

    item = AssignmentRound(
        round_id="round-1",
        academic_year="2026-2027",
        round_number=1,
        effective_from=date(2026, 8, 24),
    )

    result = repository.save(
        assignment_round=item
    )

    assert result.round_id == "round-1"
    assert result.round_number == 1
    assert result.label == "L\u1ea7n 1"

    assert (
        client.table_names[-1]
        == "assignment_rounds"
    )

    upsert_call = next(
        call
        for call in client.query.calls
        if call[0] == "upsert"
    )

    row = upsert_call[1]

    assert row["round_id"] == "round-1"
    assert row["academic_year"] == "2026-2027"
    assert row["round_number"] == 1
    assert row["effective_from"] == "2026-08-24"
    assert row["label"] == "L\u1ea7n 1"
    assert row["status"] == "ACTIVE"


def test_get_round():
    client = FakeClient(
        rows=[
            {
                "round_id": "round-2",
                "academic_year": "2026-2027",
                "round_number": 2,
                "effective_from": "2026-10-01",
                "label": "L\u1ea7n 2",
                "status": "ACTIVE",
            }
        ]
    )

    repository = (
        SupabaseAssignmentRoundRepository(
            client=client
        )
    )

    result = repository.get(
        round_id="round-2"
    )

    assert result is not None
    assert result.round_number == 2
    assert result.label == "L\u1ea7n 2"


def test_get_returns_none_when_missing():
    client = FakeClient(
        rows=[]
    )

    repository = (
        SupabaseAssignmentRoundRepository(
            client=client
        )
    )

    assert (
        repository.get(
            round_id="missing"
        )
        is None
    )


def test_list_rounds_filters_by_year():
    client = FakeClient(
        rows=[
            {
                "round_id": "round-1",
                "academic_year": "2026-2027",
                "round_number": 1,
                "effective_from": "2026-08-24",
                "label": "L\u1ea7n 1",
                "status": "ACTIVE",
            },
            {
                "round_id": "round-2",
                "academic_year": "2026-2027",
                "round_number": 2,
                "effective_from": "2026-10-01",
                "label": "L\u1ea7n 2",
                "status": "CLOSED",
            },
        ]
    )

    repository = (
        SupabaseAssignmentRoundRepository(
            client=client
        )
    )

    result = repository.list_rounds(
        academic_year="2026-2027"
    )

    assert len(result) == 2

    assert (
        ("eq", "academic_year", "2026-2027")
        in client.query.calls
    )

    assert (
        ("order", "round_number")
        in client.query.calls
    )


def test_list_rounds_filters_status():
    client = FakeClient(
        rows=[]
    )

    repository = (
        SupabaseAssignmentRoundRepository(
            client=client
        )
    )

    repository.list_rounds(
        academic_year="2026-2027",
        status=AssignmentRoundStatus.ACTIVE,
    )

    assert (
        ("eq", "status", "ACTIVE")
        in client.query.calls
    )


def test_list_rounds_rejects_invalid_status():
    client = FakeClient()

    repository = (
        SupabaseAssignmentRoundRepository(
            client=client
        )
    )

    with pytest.raises(
        TypeError,
        match="status must be AssignmentRoundStatus or None",
    ):
        repository.list_rounds(
            academic_year="2026-2027",
            status="ACTIVE",
        )


def test_delete_round():
    client = FakeClient()

    repository = (
        SupabaseAssignmentRoundRepository(
            client=client
        )
    )

    repository.delete(
        round_id="round-1"
    )

    assert (
        ("delete",)
        in client.query.calls
    )

    assert (
        ("eq", "round_id", "round-1")
        in client.query.calls
    )


def test_response_rows_rejects_non_list():
    response = SimpleNamespace(
        data={}
    )

    with pytest.raises(
        TypeError,
        match="Supabase response data must be a list",
    ):
        (
            SupabaseAssignmentRoundRepository
            ._response_rows(
                response
            )
        )


def test_response_rows_rejects_non_dict_rows():
    response = SimpleNamespace(
        data=[
            "invalid"
        ]
    )

    with pytest.raises(
        TypeError,
        match="Supabase response rows must be dict",
    ):
        (
            SupabaseAssignmentRoundRepository
            ._response_rows(
                response
            )
        )
