from __future__ import annotations

from abc import ABC
from dataclasses import FrozenInstanceError
import inspect

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


def expect_error(
    error_type,
    action,
) -> bool:
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False

    return False


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-002C - "
        "OPERATIONAL PAYLOAD BOUNDARY TEST"
    )
    print("=" * 72)

    tests = []

    reference = OperationalPayloadReference(
        source_id=" PPCT-2026 ",
        data_type=OperationalDataType.PPCT,
        payload_version=" v1 ",
    )

    tests.append((
        "OPB1 Payload reference accepted",
        isinstance(
            reference,
            OperationalPayloadReference,
        ),
    ))

    tests.append((
        "OPB2 Source ID normalized",
        reference.source_id == "PPCT-2026",
    ))

    tests.append((
        "OPB3 Data type preserved",
        reference.data_type
        is OperationalDataType.PPCT,
    ))

    tests.append((
        "OPB4 Payload version normalized",
        reference.payload_version == "v1",
    ))

    payload = (
        {
            "row": 1,
        },
        {
            "row": 2,
        },
    )

    envelope = OperationalPayloadEnvelope(
        reference=reference,
        payload=payload,
    )

    tests.append((
        "OPB5 Payload envelope accepted",
        isinstance(
            envelope,
            OperationalPayloadEnvelope,
        ),
    ))

    tests.append((
        "OPB6 Payload preserved",
        envelope.payload is payload,
    ))

    tests.append((
        "OPB7 Empty source ID blocked",
        expect_error(
            ValueError,
            lambda: OperationalPayloadReference(
                source_id=" ",
                data_type=OperationalDataType.PPCT,
            ),
        ),
    ))

    tests.append((
        "OPB8 Wrong data type blocked",
        expect_error(
            TypeError,
            lambda: OperationalPayloadReference(
                source_id="SRC",
                data_type="PPCT",
            ),
        ),
    ))

    tests.append((
        "OPB9 None payload blocked",
        expect_error(
            ValueError,
            lambda: OperationalPayloadEnvelope(
                reference=reference,
                payload=None,
            ),
        ),
    ))

    tests.append((
        "OPB10 Wrong reference type blocked",
        expect_error(
            TypeError,
            lambda: OperationalPayloadEnvelope(
                reference="bad-reference",
                payload=payload,
            ),
        ),
    ))

    tests.append((
        "OPB11 Payload reference immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                reference,
                "source_id",
                "CHANGED",
            ),
        ),
    ))

    tests.append((
        "OPB12 Payload envelope immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                envelope,
                "payload",
                (),
            ),
        ),
    ))

    tests.append((
        "OPB13 Repository is abstract",
        issubclass(
            OperationalPayloadRepository,
            ABC,
        ),
    ))

    tests.append((
        "OPB14 Repository capabilities locked",
        (
            OperationalPayloadRepository
            .__abstractmethods__
        )
        == {
            "save",
            "get",
            "delete",
        },
    ))

    tests.append((
        "OPB15 Abstract repository cannot instantiate",
        _cannot_instantiate(),
    ))

    repository_source = inspect.getsource(
        OperationalPayloadRepository
    )

    forbidden_storage_tokens = (
        "sqlite3",
        "supabase",
        "openpyxl",
        "streamlit",
        "googleapiclient",
        ".xlsx",
        ".docx",
        "Path(",
        "open(",
        "SELECT ",
        "INSERT ",
        "UPDATE ",
    )

    tests.append((
        "OPB16 Repository owns no physical storage dependency",
        not any(
            token.lower()
            in repository_source.lower()
            for token
            in forbidden_storage_tokens
        ),
    ))

    payload_source = (
        inspect.getsource(
            OperationalPayloadReference
        )
        + inspect.getsource(
            OperationalPayloadEnvelope
        )
    )

    tests.append((
        "OPB17 Payload boundary owns no physical storage dependency",
        not any(
            token.lower()
            in payload_source.lower()
            for token
            in forbidden_storage_tokens
        ),
    ))

    tests.append((
        "OPB18 Boundary contains no fixed educational values",
        not any(
            token
            in payload_source
            for token in (
                "140",
                "105",
                "70",
                "35",
                "KNTT",
                "Toán 6",
            )
        ),
    ))

    future_reference = OperationalPayloadReference(
        source_id="FUTURE",
        data_type=OperationalDataType.TIMETABLE,
    )

    tests.append((
        "OPB19 Boundary remains data-type neutral",
        future_reference.data_type
        is OperationalDataType.TIMETABLE,
    ))

    tests.append((
        "OPB20 Catalog metadata and payload remain separate",
        (
            not hasattr(
                envelope,
                "academic_year",
            )
            and
            not hasattr(
                envelope,
                "owner_id",
            )
            and
            not hasattr(
                envelope,
                "status",
            )
        ),
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
            "RESULT: PASS - OPERATIONAL "
            "PAYLOAD BOUNDARY VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - OPERATIONAL "
        "PAYLOAD BOUNDARY VIOLATED"
    )

    return False


def _cannot_instantiate() -> bool:
    try:
        OperationalPayloadRepository()
    except TypeError:
        return True

    return False


def test_operational_payload_boundary():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
