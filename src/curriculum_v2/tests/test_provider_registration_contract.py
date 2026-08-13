from dataclasses import FrozenInstanceError

from curriculum_v2.providers.contracts import (
    ProviderRegistration,
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
        "WR-001D.11D.1 - PROVIDER "
        "REGISTRATION CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    metadata_input = {
        "owner": "canonical-data",
    }

    registration = ProviderRegistration(
        provider_id=" PROVIDER-A ",
        capabilities=(
            " curriculum ",
            "learning_requirements",
            "curriculum",
        ),
        priority=10,
        enabled=True,
        metadata=metadata_input,
    )

    checks = [
        (
            "PRC1 Valid registration accepted",
            registration.provider_id
            == "PROVIDER-A",
        ),
        (
            "PRC2 Capabilities normalized",
            registration.capabilities
            == (
                "curriculum",
                "learning_requirements",
            ),
        ),
        (
            "PRC3 Duplicate capabilities removed",
            len(registration.capabilities)
            == 2,
        ),
        (
            "PRC4 Capability support detected",
            registration.supports(
                " curriculum "
            ),
        ),
        (
            "PRC5 Unknown capability rejected",
            not registration.supports(
                "future_capability"
            ),
        ),
        (
            "PRC6 Empty provider ID blocked",
            expect_error(
                ValueError,
                lambda: ProviderRegistration(
                    provider_id=" ",
                    capabilities=("X",),
                ),
            ),
        ),
        (
            "PRC7 Empty capabilities blocked",
            expect_error(
                ValueError,
                lambda: ProviderRegistration(
                    provider_id="P",
                    capabilities=(),
                ),
            ),
        ),
        (
            "PRC8 Non-tuple capabilities blocked",
            expect_error(
                TypeError,
                lambda: ProviderRegistration(
                    provider_id="P",
                    capabilities=["X"],
                ),
            ),
        ),
        (
            "PRC9 Invalid priority blocked",
            expect_error(
                ValueError,
                lambda: ProviderRegistration(
                    provider_id="P",
                    capabilities=("X",),
                    priority=-1,
                ),
            ),
        ),
        (
            "PRC10 Boolean priority blocked",
            expect_error(
                TypeError,
                lambda: ProviderRegistration(
                    provider_id="P",
                    capabilities=("X",),
                    priority=True,
                ),
            ),
        ),
        (
            "PRC11 Invalid enabled blocked",
            expect_error(
                TypeError,
                lambda: ProviderRegistration(
                    provider_id="P",
                    capabilities=("X",),
                    enabled=1,
                ),
            ),
        ),
    ]

    metadata_input["owner"] = "changed"

    checks.append(
        (
            "PRC12 Metadata input isolated",
            registration.metadata["owner"]
            == "canonical-data",
        )
    )

    try:
        registration.metadata["owner"] = "X"
        metadata_immutable = False
    except TypeError:
        metadata_immutable = True

    checks.append(
        (
            "PRC13 Metadata immutable",
            metadata_immutable,
        )
    )

    try:
        registration.provider_id = "X"
        contract_immutable = False
    except FrozenInstanceError:
        contract_immutable = True
    except Exception:
        contract_immutable = True

    checks.append(
        (
            "PRC14 Registration immutable",
            contract_immutable,
        )
    )

    disabled = ProviderRegistration(
        provider_id="P-DISABLED",
        capabilities=("future_capability",),
        enabled=False,
    )

    checks.append(
        (
            "PRC15 Disabled provider unavailable",
            not disabled.supports(
                "future_capability"
            ),
        )
    )

    future = ProviderRegistration(
        provider_id="P-FUTURE",
        capabilities=(
            "future_educational_capability",
        ),
    )

    checks.append(
        (
            "PRC16 New capability requires no "
            "contract modification",
            future.supports(
                "future_educational_capability"
            ),
        )
    )

    for label, passed in checks:
        results.append(passed)

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - PROVIDER "
            "REGISTRATION CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - PROVIDER "
            "REGISTRATION CONTRACT VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
