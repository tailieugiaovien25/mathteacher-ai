from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from educational_planning_v2.models.operational_data_source import (
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
    OperationalPayloadReference,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)
from educational_planning_v2.repositories.operational_payload_repository import (
    OperationalPayloadRepository,
)
from educational_planning_v2.services.ppct_import_service import (
    PPCTImportRequest,
    PPCTImportService,
)


class MemorySourceRepository(
    OperationalDataSourceRepository
):
    def __init__(self) -> None:
        self.sources = {}
        self.saved_statuses = []

    def save(
        self,
        *,
        source: OperationalDataSource,
    ) -> OperationalDataSource:
        self.sources[source.source_id] = source
        self.saved_statuses.append(
            source.status
        )
        return source

    def get(
        self,
        *,
        source_id: str,
    ) -> OperationalDataSource | None:
        return self.sources.get(
            source_id
        )

    def list_sources(
        self,
        *,
        owner_id=None,
        academic_year=None,
        data_type=None,
        status=None,
    ) -> tuple[OperationalDataSource, ...]:
        values = tuple(
            self.sources.values()
        )

        if owner_id is not None:
            values = tuple(
                source
                for source in values
                if source.owner_id == owner_id
            )

        if academic_year is not None:
            values = tuple(
                source
                for source in values
                if source.academic_year
                == academic_year
            )

        if data_type is not None:
            values = tuple(
                source
                for source in values
                if source.data_type
                is data_type
            )

        if status is not None:
            values = tuple(
                source
                for source in values
                if source.status
                is status
            )

        return values

    def delete(
        self,
        *,
        source_id: str,
    ) -> None:
        self.sources.pop(
            source_id,
            None,
        )


class MemoryPayloadRepository(
    OperationalPayloadRepository
):
    def __init__(self) -> None:
        self.envelopes = {}

    @staticmethod
    def _key(
        reference: OperationalPayloadReference,
    ):
        return (
            reference.source_id,
            reference.data_type,
            reference.payload_version,
        )

    def save(
        self,
        *,
        envelope: OperationalPayloadEnvelope,
    ) -> OperationalPayloadEnvelope:
        self.envelopes[
            self._key(envelope.reference)
        ] = envelope

        return envelope

    def get(
        self,
        *,
        reference: OperationalPayloadReference,
    ) -> OperationalPayloadEnvelope | None:
        return self.envelopes.get(
            self._key(reference)
        )

    def delete(
        self,
        *,
        reference: OperationalPayloadReference,
    ) -> None:
        self.envelopes.pop(
            self._key(reference),
            None,
        )


def _workbook_bytes() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active

    worksheet.append(
        [
            "M\u00f4n/L\u1edbp",
            "Ti\u1ebft",
            "T\u00ean b\u00e0i h\u1ecdc",
        ]
    )

    worksheet.append(
        [
            "To\u00e1n 6",
            1,
            "B\u00e0i th\u1ee9 nh\u1ea5t",
        ]
    )

    worksheet.append(
        [
            "To\u00e1n 6",
            2,
            "B\u00e0i th\u1ee9 hai",
        ]
    )

    buffer = BytesIO()

    workbook.save(buffer)
    workbook.close()

    return buffer.getvalue()


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-003B.5D.1C - "
        "PPCT IMPORT LIFECYCLE SERVICE TEST"
    )
    print("=" * 72)

    source_repository = (
        MemorySourceRepository()
    )

    payload_repository = (
        MemoryPayloadRepository()
    )

    service = PPCTImportService(
        source_repository=source_repository,
        payload_repository=payload_repository,
    )

    result = service.import_workbook(
        request=PPCTImportRequest(
            owner_id="teacher-001",
            academic_year="2026-2027",
            source_id="ppct-import-001",
            source_name="PPCT upload test",
            source_version="v1",
        ),
        workbook_bytes=_workbook_bytes(),
    )

    tests = []

    tests.append((
        "PPCTI1 Result source ACTIVE",
        result.source.status
        is OperationalDataStatus.ACTIVE,
    ))

    tests.append((
        "PPCTI2 Data type PPCT",
        result.source.data_type
        is OperationalDataType.PPCT,
    ))

    tests.append((
        "PPCTI3 Owner preserved",
        result.source.owner_id
        == "teacher-001",
    ))

    tests.append((
        "PPCTI4 Academic year preserved",
        result.source.academic_year
        == "2026-2027",
    ))

    tests.append((
        "PPCTI5 Source identity preserved",
        result.source.source_id
        == "ppct-import-001",
    ))

    tests.append((
        "PPCTI6 Lifecycle order preserved",
        source_repository.saved_statuses
        == [
            OperationalDataStatus.UPLOADED,
            OperationalDataStatus.MAPPED,
            OperationalDataStatus.VALIDATED,
            OperationalDataStatus.ACTIVE,
        ],
    ))

    tests.append((
        "PPCTI7 Payload persisted",
        len(
            payload_repository.envelopes
        ) == 1,
    ))

    tests.append((
        "PPCTI8 Payload source matches metadata",
        result.envelope.reference.source_id
        == result.source.source_id,
    ))

    tests.append((
        "PPCTI9 Payload type matches metadata",
        result.envelope.reference.data_type
        is result.source.data_type,
    ))

    tests.append((
        "PPCTI10 Workbook rows preserved",
        len(result.envelope.payload) == 2,
    ))

    stored = source_repository.get(
        source_id="ppct-import-001",
    )

    tests.append((
        "PPCTI11 Repository ends ACTIVE",
        stored is not None
        and stored.status
        is OperationalDataStatus.ACTIVE,
    ))

    invalid_request_blocked = False

    try:
        service.import_workbook(
            request="bad-request",
            workbook_bytes=_workbook_bytes(),
        )
    except TypeError:
        invalid_request_blocked = True

    tests.append((
        "PPCTI12 Invalid request blocked",
        invalid_request_blocked,
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
            "RESULT: PASS - PPCT IMPORT "
            "LIFECYCLE SERVICE VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - PPCT IMPORT "
        "LIFECYCLE SERVICE VIOLATED"
    )

    return False


def test_ppct_import_service():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
