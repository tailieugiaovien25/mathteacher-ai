from types import SimpleNamespace

import pytest

from portal_v2.runtime.system_weekly_schedule_runtime import (
    SystemActivePpctSnapshot,
    SystemWeeklyScheduleRuntime,
)


class _SourceRepository:
    def __init__(self, sources):
        self.sources = sources
        self.calls = []

    def list_sources(self, **kwargs):
        self.calls.append(kwargs)
        return self.sources


class _PayloadRepository:
    def __init__(self, payload):
        self.payload = payload
        self.references = []

    def get(self, *, reference):
        self.references.append(reference)
        return SimpleNamespace(payload=self.payload)


def _runtime(*, sources, payload):
    runtime = object.__new__(SystemWeeklyScheduleRuntime)
    runtime._user_id = "teacher-001"
    runtime._source_repository = _SourceRepository(sources)
    runtime._payload_repository = _PayloadRepository(payload)
    return runtime


def _source(*, source_id="ppct-2026", source_version="7"):
    return SimpleNamespace(
        source_id=source_id,
        source_version=source_version,
    )


def test_public_snapshot_returns_rows_and_provenance():
    runtime = _runtime(
        sources=[_source()],
        payload=[
            {
                "subject_grade": "Toan 8",
                "period": 1,
                "lesson_name": "Bai 1",
                "sub_subject": None,
            },
            {
                "subject_grade": "Toan 8",
                "period": 2,
                "lesson_name": "Bai 2",
                "sub_subject": None,
            },
        ],
    )

    snapshot = runtime.load_active_ppct_snapshot(
        academic_year="2026-2027",
    )

    assert isinstance(snapshot, SystemActivePpctSnapshot)
    assert snapshot.academic_year == "2026-2027"
    assert snapshot.source_id == "ppct-2026"
    assert snapshot.source_version == "7"
    assert [row.period for row in snapshot.rows] == [1, 2]


def test_existing_private_row_loader_delegates_to_snapshot_contract():
    runtime = _runtime(
        sources=[_source()],
        payload=[
            {
                "subject_grade": "Toan 8",
                "period": 37,
                "lesson_name": "Kiem tra giua hoc ky I",
            },
        ],
    )

    rows = runtime._load_active_ppct_rows(
        academic_year="2026-2027",
    )

    assert len(rows) == 1
    assert rows[0].period == 37


def test_multiple_active_ppct_sources_fail_closed():
    runtime = _runtime(
        sources=[
            _source(source_id="ppct-a"),
            _source(source_id="ppct-b"),
        ],
        payload=[],
    )

    with pytest.raises(
        ValueError,
        match="exactly one ACTIVE PPCT",
    ):
        runtime.load_active_ppct_snapshot(
            academic_year="2026-2027",
        )


def test_missing_payload_fails_closed():
    runtime = object.__new__(SystemWeeklyScheduleRuntime)
    runtime._user_id = "teacher-001"
    runtime._source_repository = _SourceRepository([_source()])

    class _MissingPayload:
        def get(self, *, reference):
            return None

    runtime._payload_repository = _MissingPayload()

    with pytest.raises(
        LookupError,
        match="ACTIVE PPCT payload not found",
    ):
        runtime.load_active_ppct_snapshot(
            academic_year="2026-2027",
        )
