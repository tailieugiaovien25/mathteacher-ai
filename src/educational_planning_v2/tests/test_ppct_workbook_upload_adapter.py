from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from educational_planning_v2.adapters.ppct_workbook_upload_adapter import (
    PPCTWorkbookUploadAdapter,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataType,
)


def _workbook_bytes() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active

    worksheet.append(
        ["PH\u00c2N PH\u1ed0I CH\u01af\u01a0NG TR\u00ccNH"]
    )
    worksheet.append(
        []
    )
    worksheet.append(
        [
            "M\u00f4n/L\u1edbp",
            "Ph\u00e2n m\u00f4n",
            "Ti\u1ebft",
            "T\u00ean b\u00e0i h\u1ecdc",
        ]
    )
    worksheet.append(
        [
            "To\u00e1n 6",
            "S\u1ed1 h\u1ecdc",
            1,
            "B\u00e0i th\u1ee9 nh\u1ea5t",
        ]
    )
    worksheet.append(
        [
            "To\u00e1n 6",
            "H\u00ecnh h\u1ecdc",
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
        "MVP-OPS-003B.5D.1B - "
        "PPCT WORKBOOK UPLOAD BOUNDARY TEST"
    )
    print("=" * 72)

    adapter = PPCTWorkbookUploadAdapter()

    rows = adapter.parse(
        workbook_bytes=_workbook_bytes(),
    )

    tests = []

    tests.append((
        "PPCTU1 Workbook parsed",
        len(rows) == 2,
    ))

    tests.append((
        "PPCTU2 Output uses PPCTRow",
        all(
            isinstance(row, PPCTRow)
            for row in rows
        ),
    ))

    tests.append((
        "PPCTU3 Subject/grade preserved",
        rows[0].subject_grade
        == "To\u00e1n 6",
    ))

    tests.append((
        "PPCTU4 Sub-subject preserved",
        rows[0].sub_subject
        == "S\u1ed1 h\u1ecdc",
    ))

    tests.append((
        "PPCTU5 Period preserved",
        rows[0].period == 1,
    ))

    tests.append((
        "PPCTU6 Lesson name preserved",
        rows[0].lesson_name
        == "B\u00e0i th\u1ee9 nh\u1ea5t",
    ))

    envelope = adapter.build_envelope(
        workbook_bytes=_workbook_bytes(),
        source_id=" ppct-upload-001 ",
        payload_version=" v1 ",
    )

    tests.append((
        "PPCTU7 Envelope created",
        envelope.reference.source_id
        == "ppct-upload-001",
    ))

    tests.append((
        "PPCTU8 Envelope data type PPCT",
        envelope.reference.data_type
        is OperationalDataType.PPCT,
    ))

    tests.append((
        "PPCTU9 Payload version normalized",
        envelope.reference.payload_version
        == "v1",
    ))

    tests.append((
        "PPCTU10 Payload JSON-compatible structure",
        envelope.payload
        == (
            {
                "subject_grade": "To\u00e1n 6",
                "period": 1,
                "lesson_name": "B\u00e0i th\u1ee9 nh\u1ea5t",
                "sub_subject": "S\u1ed1 h\u1ecdc",
            },
            {
                "subject_grade": "To\u00e1n 6",
                "period": 2,
                "lesson_name": "B\u00e0i th\u1ee9 hai",
                "sub_subject": "H\u00ecnh h\u1ecdc",
            },
        ),
    ))

    invalid_bytes_blocked = False

    try:
        adapter.parse(
            workbook_bytes=b"",
        )
    except ValueError:
        invalid_bytes_blocked = True

    tests.append((
        "PPCTU11 Empty workbook blocked",
        invalid_bytes_blocked,
    ))

    wrong_type_blocked = False

    try:
        adapter.parse(
            workbook_bytes="bad",
        )
    except TypeError:
        wrong_type_blocked = True

    tests.append((
        "PPCTU12 Non-bytes input blocked",
        wrong_type_blocked,
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
            "RESULT: PASS - PPCT WORKBOOK "
            "UPLOAD BOUNDARY VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - PPCT WORKBOOK "
        "UPLOAD BOUNDARY VIOLATED"
    )

    return False


def test_ppct_workbook_upload_adapter():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
