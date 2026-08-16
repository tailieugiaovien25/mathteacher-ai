from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.adapters.supabase_operational_payload_repository import (
    SupabaseOperationalPayloadRepository,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
    OperationalPayloadReference,
)
from educational_planning_v2.repositories.operational_payload_repository import (
    OperationalPayloadRepository,
)


@dataclass
class _Response:
    data: list[dict]


class _Request:
    def __init__(
        self,
        table,
        mode,
        row=None,
    ):
        self.table = table
        self.mode = mode
        self.row = row
        self.filters = {}

    def select(self, *_args, **_kwargs):
        self.mode = "select"
        return self

    def delete(self):
        self.mode = "delete"
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def limit(self, _value):
        return self

    def execute(self):
        if self.mode == "upsert":
            identity = (
                self.row["user_id"],
                self.row["source_id"],
                self.row["data_type"],
                self.row["payload_version"],
            )

            self.table.rows[
                identity
            ] = dict(self.row)

            return _Response(
                [dict(self.row)]
            )

        matching = [
            row
            for row in self.table.rows.values()
            if all(
                row.get(key) == value
                for key, value
                in self.filters.items()
            )
        ]

        if self.mode == "delete":
            identities = [
                key
                for key, row
                in self.table.rows.items()
                if all(
                    row.get(filter_key)
                    == filter_value
                    for filter_key, filter_value
                    in self.filters.items()
                )
            ]

            removed = [
                self.table.rows.pop(
                    key
                )
                for key in identities
            ]

            return _Response(
                removed
            )

        return _Response(
            [dict(row) for row in matching]
        )


class _Table:
    def __init__(self):
        self.rows = {}

    def upsert(
        self,
        row,
        on_conflict=None,
    ):
        assert (
            on_conflict
            ==
            "user_id,source_id,"
            "data_type,payload_version"
        )

        return _Request(
            self,
            "upsert",
            row,
        )

    def select(self, *_args):
        return _Request(
            self,
            "select",
        )

    def delete(self):
        return _Request(
            self,
            "delete",
        )


class _Client:
    def __init__(self):
        self.tables = {}

    def table(self, name):
        if name not in self.tables:
            self.tables[name] = _Table()

        return self.tables[name]


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-003B.5D.1A - "
        "SUPABASE OPERATIONAL PAYLOAD REPOSITORY TEST"
    )
    print("=" * 72)

    client = _Client()

    repository = (
        SupabaseOperationalPayloadRepository(
            client=client,
            user_id=" teacher-001 ",
        )
    )

    reference = OperationalPayloadReference(
        source_id="ppct-2026",
        data_type=OperationalDataType.PPCT,
        payload_version="v1",
    )

    payload = (
        {
            "subject_grade": "To?n 6",
            "period": 1,
            "lesson_name": "B?i th? nghi?m",
        },
    )

    envelope = OperationalPayloadEnvelope(
        reference=reference,
        payload=payload,
    )

    tests = []

    tests.append((
        "SOPR1 Adapter implements repository port",
        isinstance(
            repository,
            OperationalPayloadRepository,
        ),
    ))

    tests.append((
        "SOPR2 User ID normalized",
        repository.user_id
        == "teacher-001",
    ))

    saved = repository.save(
        envelope=envelope,
    )

    tests.append((
        "SOPR3 Save returns envelope",
        isinstance(
            saved,
            OperationalPayloadEnvelope,
        ),
    ))

    tests.append((
        "SOPR4 Source identity preserved",
        saved.reference.source_id
        == "ppct-2026",
    ))

    tests.append((
        "SOPR5 Data type preserved",
        saved.reference.data_type
        is OperationalDataType.PPCT,
    ))

    tests.append((
        "SOPR6 Payload version preserved",
        saved.reference.payload_version
        == "v1",
    ))

    tests.append((
        "SOPR7 Payload preserved",
        saved.payload
        == payload,
    ))

    loaded = repository.get(
        reference=reference,
    )

    tests.append((
        "SOPR8 Get returns stored envelope",
        (
            loaded is not None
            and
            loaded.reference
            == reference
        ),
    ))

    tests.append((
        "SOPR9 Missing payload returns None",
        repository.get(
            reference=OperationalPayloadReference(
                source_id="missing",
                data_type=OperationalDataType.PPCT,
                payload_version="v1",
            )
        )
        is None,
    ))

    updated = OperationalPayloadEnvelope(
        reference=reference,
        payload=(
            {
                "subject_grade": "To?n 6",
                "period": 2,
                "lesson_name": "B?i c?p nh?t",
            },
        ),
    )

    repository.save(
        envelope=updated,
    )

    reloaded = repository.get(
        reference=reference,
    )

    tests.append((
        "SOPR10 Upsert updates same identity",
        (
            reloaded is not None
            and
            reloaded.payload
            == updated.payload
        ),
    ))

    invalid_blocked = False

    try:
        repository.save(
            envelope=OperationalPayloadEnvelope(
                reference=reference,
                payload=object(),
            )
        )
    except TypeError:
        invalid_blocked = True

    tests.append((
        "SOPR11 Non-JSON payload blocked",
        invalid_blocked,
    ))

    repository.delete(
        reference=reference,
    )

    tests.append((
        "SOPR12 Delete removes payload",
        repository.get(
            reference=reference,
        )
        is None,
    ))

    tests.append((
        "SOPR13 Catalog metadata remains separate",
        (
            not hasattr(
                envelope,
                "owner_id",
            )
            and
            not hasattr(
                envelope,
                "academic_year",
            )
            and
            not hasattr(
                envelope,
                "status",
            )
        ),
    ))

    migration = (
        __import__("pathlib")
        .Path(
            "supabase/migrations/"
            "202608160002_operational_payloads.sql"
        )
        .read_text(
            encoding="utf-8"
        )
        .lower()
    )

    tests.append((
        "SOPR14 Payload table declared",
        (
            "create table if not exists "
            "public.operational_payloads"
        )
        in migration,
    ))

    tests.append((
        "SOPR15 JSONB payload storage declared",
        "payload jsonb not null"
        in migration,
    ))

    tests.append((
        "SOPR16 Authenticated CRUD grant exists",
        (
            "grant select, insert, update, delete"
            in migration
            and
            "to authenticated"
            in migration
        ),
    ))

    tests.append((
        "SOPR17 RLS enabled",
        "enable row level security"
        in migration,
    ))

    results = []

    for label, passed in tests:
        results.append(passed)
        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - SUPABASE OPERATIONAL "
            "PAYLOAD REPOSITORY VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - SUPABASE OPERATIONAL "
        "PAYLOAD REPOSITORY VIOLATED"
    )

    return False


def test_supabase_operational_payload_repository():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
