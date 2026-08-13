import inspect

from curriculum_v2.providers import (
    CapabilityEducationalDataProvider,
    EducationalDataProvider,
)
from curriculum_v2.providers.contracts import (
    EducationalDataProvenance,
    EducationalDataQuery,
    EducationalDataResult,
    EducationalDataVersion,
)


def make_result(
    query,
):
    return EducationalDataResult(
        capability=query.capability,
        data=("DATA",),
        provenance=EducationalDataProvenance(
            source_id="SOURCE",
            authority_type="TEST",
            status="CANDIDATE",
        ),
        version=EducationalDataVersion(
            version_id="V1",
        ),
    )


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
        "WR-001D.12A - CAPABILITY EDUCATIONAL "
        "DATA PROVIDER TEST"
    )
    print("=" * 72)

    results = []

    provider = CapabilityEducationalDataProvider(
        handlers={
            "curriculum": make_result,
            "future_capability": make_result,
        }
    )

    checks = [
        (
            "CEDP1 Provider implements stable contract",
            isinstance(
                provider,
                EducationalDataProvider,
            ),
        ),
        (
            "CEDP2 Capabilities exposed deterministically",
            provider.capabilities
            == (
                "curriculum",
                "future_capability",
            ),
        ),
        (
            "CEDP3 Generic query resolved",
            provider.query(
                EducationalDataQuery(
                    capability="future_capability",
                )
            ).data
            == ("DATA",),
        ),
        (
            "CEDP4 Compatibility curriculum call works",
            provider.get_curriculum(
                curriculum_ref="CURRICULUM-X",
            ).capability
            == "curriculum",
        ),
        (
            "CEDP5 Unknown capability blocked",
            expect_error(
                LookupError,
                lambda: provider.query(
                    EducationalDataQuery(
                        capability="UNKNOWN",
                    )
                ),
            ),
        ),
        (
            "CEDP6 Wrong query type blocked",
            expect_error(
                TypeError,
                lambda: provider.query(
                    "bad"
                ),
            ),
        ),
        (
            "CEDP7 Empty handler set blocked",
            expect_error(
                ValueError,
                lambda: CapabilityEducationalDataProvider(
                    handlers={}
                ),
            ),
        ),
        (
            "CEDP8 Invalid handler blocked",
            expect_error(
                TypeError,
                lambda: CapabilityEducationalDataProvider(
                    handlers={
                        "X": "bad",
                    }
                ),
            ),
        ),
    ]

    def wrong_result(
        query,
    ):
        return "bad"

    bad_provider = (
        CapabilityEducationalDataProvider(
            handlers={
                "X": wrong_result,
            }
        )
    )

    checks.append(
        (
            "CEDP9 Invalid handler result blocked",
            expect_error(
                TypeError,
                lambda: bad_provider.query(
                    EducationalDataQuery(
                        capability="X",
                    )
                ),
            ),
        )
    )

    def mismatched_result(
        query,
    ):
        return EducationalDataResult(
            capability="OTHER",
            data=(),
            provenance=EducationalDataProvenance(
                source_id="SOURCE",
                authority_type="TEST",
            ),
            version=EducationalDataVersion(
                version_id="V1",
            ),
        )

    mismatch_provider = (
        CapabilityEducationalDataProvider(
            handlers={
                "X": mismatched_result,
            }
        )
    )

    checks.append(
        (
            "CEDP10 Capability mismatch blocked",
            expect_error(
                ValueError,
                lambda: mismatch_provider.query(
                    EducationalDataQuery(
                        capability="X",
                    )
                ),
            ),
        )
    )

    future_provider = (
        CapabilityEducationalDataProvider(
            handlers={
                "brand_new_capability":
                    make_result,
            }
        )
    )

    checks.append(
        (
            "CEDP11 Future capability needs no provider change",
            future_provider.query(
                EducationalDataQuery(
                    capability="brand_new_capability",
                )
            ).capability
            == "brand_new_capability",
        )
    )

    for label, passed in checks:
        results.append(
            passed
        )

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    source = inspect.getsource(
        CapabilityEducationalDataProvider
    ).lower()

    forbidden = (
        "140",
        "2018",
        "5512",
        "7991",
        "kntt",
        "kết nối tri thức",
        "lbg-tuyen",
        ".xlsm",
        ".xlsx",
        "openpyxl",
        "load_workbook",
        "data/input/",
    )

    violations = [
        token
        for token in forbidden
        if token in source
    ]

    passed = not violations
    results.append(
        passed
    )

    print(
        "CEDP12 Provider data-independence guard: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if violations:
        print(
            "VIOLATIONS:",
            violations,
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - CAPABILITY EDUCATIONAL "
            "DATA PROVIDER VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - CAPABILITY EDUCATIONAL "
            "DATA PROVIDER VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
