from curriculum_v2.governance import (
    InMemoryTrustedAdministrativeDataRepository,
    TrustedAdministrativeDataRepository,
)


class SampleRecordA:
    def __init__(
        self,
        value,
    ):
        self.value = value


class SampleRecordB:
    def __init__(
        self,
        value,
    ):
        self.value = value


def expect_error(
    error_type,
    action,
):
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False

    return False


def main():
    print("=" * 72)
    print(
        "WR-001D.12C.6A.3 - "
        "IN-MEMORY TRUSTED ADMIN DATA REPOSITORY TEST"
    )
    print("=" * 72)

    results = []

    repository = (
        InMemoryTrustedAdministrativeDataRepository()
    )

    tests = []

    tests.append((
        "IMR1 Implements repository contract",
        isinstance(
            repository,
            TrustedAdministrativeDataRepository,
        ),
    ))

    record_a1 = SampleRecordA(
        "A1"
    )

    repository.save(
        record_id="REC-A1",
        record=record_a1,
    )

    tests.append((
        "IMR2 Record saved",
        repository.get(
            record_id="REC-A1"
        )
        is record_a1,
    ))

    record_a2 = SampleRecordA(
        "A2"
    )

    record_b1 = SampleRecordB(
        "B1"
    )

    repository.save(
        record_id="REC-A2",
        record=record_a2,
    )

    repository.save(
        record_id="REC-B1",
        record=record_b1,
    )

    tests.append((
        "IMR3 All records listed",
        repository.list_records()
        == (
            record_a1,
            record_a2,
            record_b1,
        ),
    ))

    tests.append((
        "IMR4 Logical type filter works",
        repository.list_records(
            record_type="SampleRecordA"
        )
        == (
            record_a1,
            record_a2,
        ),
    ))

    replacement = SampleRecordA(
        "REPLACED"
    )

    repository.save(
        record_id="REC-A1",
        record=replacement,
    )

    tests.append((
        "IMR5 Save replaces same logical identity",
        repository.get(
            record_id="REC-A1"
        )
        is replacement,
    ))

    repository.delete(
        record_id="REC-A2"
    )

    tests.append((
        "IMR6 Delete removes record",
        repository.get(
            record_id="REC-A2"
        )
        is None,
    ))

    repository.delete(
        record_id="DOES-NOT-EXIST"
    )

    tests.append((
        "IMR7 Delete missing record is safe",
        True,
    ))

    tests.append((
        "IMR8 Missing record returns none",
        repository.get(
            record_id="UNKNOWN"
        )
        is None,
    ))

    tests.append((
        "IMR9 Empty record ID blocked",
        expect_error(
            ValueError,
            lambda: repository.get(
                record_id=" "
            ),
        ),
    ))

    tests.append((
        "IMR10 Wrong record ID type blocked",
        expect_error(
            TypeError,
            lambda: repository.get(
                record_id=123
            ),
        ),
    ))

    tests.append((
        "IMR11 Empty record type blocked",
        expect_error(
            ValueError,
            lambda: repository.list_records(
                record_type=" "
            ),
        ),
    ))

    tests.append((
        "IMR12 Wrong record type blocked",
        expect_error(
            TypeError,
            lambda: repository.list_records(
                record_type=123
            ),
        ),
    ))

    repository_two = (
        InMemoryTrustedAdministrativeDataRepository()
    )

    tests.append((
        "IMR13 Repository instances isolated",
        repository_two.list_records()
        == (),
    ))

    tests.append((
        "IMR14 Storage implementation contains no educational values",
        all(
            value not in (
                140,
                105,
                70,
                35,
            )
            for value in (
                repository.__dict__.values()
            )
        ),
    ))

    for label, passed in tests:
        results.append(
            passed
        )

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - IN-MEMORY TRUSTED "
            "ADMIN DATA REPOSITORY VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - IN-MEMORY TRUSTED "
        "ADMIN DATA REPOSITORY VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
