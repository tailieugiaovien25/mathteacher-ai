import inspect

from curriculum_v2.providers import (
    EducationalDataProvider,
    EducationalDataProviderRegistry,
    RegisteredEducationalDataProvider,
)
from curriculum_v2.providers.contracts import (
    EducationalDataProvenance,
    EducationalDataQuery,
    EducationalDataResult,
    EducationalDataVersion,
    ProviderRegistration,
)


class FakeProvider(
    EducationalDataProvider
):
    def __init__(
        self,
        provider_name: str,
    ) -> None:
        self.provider_name = provider_name

    def query(
        self,
        query: EducationalDataQuery,
    ) -> EducationalDataResult:
        return EducationalDataResult(
            capability=query.capability,
            data=(
                self.provider_name,
            ),
            provenance=EducationalDataProvenance(
                source_id=self.provider_name,
                authority_type="TEST",
                status="CANDIDATE",
            ),
            version=EducationalDataVersion(
                version_id="TEST-V1",
            ),
        )

    def get_curriculum(
        self,
        *,
        curriculum_ref: str,
    ):
        return curriculum_ref

    def get_learning_requirements(
        self,
        *,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ):
        return ()

    def get_textbook_lessons(
        self,
        *,
        textbook_ref: str,
        subject: str,
        grade: int,
    ):
        return ()

    def get_textbook_requirement_mappings(
        self,
        *,
        textbook_ref: str,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ):
        return ()

    def get_time_allocation(
        self,
        *,
        curriculum_ref: str,
        subject: str,
        grade: int,
    ):
        return None


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
        "WR-001D.11D.2 - EDUCATIONAL DATA "
        "PROVIDER REGISTRY TEST"
    )
    print("=" * 72)

    results = []

    registry = (
        EducationalDataProviderRegistry()
    )

    provider_a = FakeProvider(
        "PROVIDER-A"
    )

    provider_b = FakeProvider(
        "PROVIDER-B"
    )

    provider_disabled = FakeProvider(
        "PROVIDER-DISABLED"
    )

    registration_a = ProviderRegistration(
        provider_id="PROVIDER-A",
        capabilities=(
            "curriculum",
            "future_capability",
        ),
        priority=20,
    )

    registration_b = ProviderRegistration(
        provider_id="PROVIDER-B",
        capabilities=(
            "curriculum",
        ),
        priority=10,
    )

    registration_disabled = (
        ProviderRegistration(
            provider_id="PROVIDER-DISABLED",
            capabilities=(
                "curriculum",
            ),
            priority=1,
            enabled=False,
        )
    )

    registry.register(
        registration=registration_a,
        provider=provider_a,
    )

    registry.register(
        registration=registration_b,
        provider=provider_b,
    )

    registry.register(
        registration=registration_disabled,
        provider=provider_disabled,
    )

    checks = [
        (
            "EDPR1 Provider registered",
            registry.get(
                provider_id="PROVIDER-A",
            ).provider
            is provider_a,
        ),
        (
            "EDPR2 Registration identity preserved",
            registry.get(
                provider_id="PROVIDER-A",
            ).registration
            is registration_a,
        ),
        (
            "EDPR3 Capability discovery works",
            len(
                registry.providers_for_capability(
                    capability="curriculum",
                )
            )
            == 2,
        ),
        (
            "EDPR4 Disabled provider excluded",
            all(
                entry.registration.provider_id
                != "PROVIDER-DISABLED"
                for entry
                in registry.providers_for_capability(
                    capability="curriculum",
                )
            ),
        ),
        (
            "EDPR5 Lowest priority value selected",
            registry.resolve(
                capability="curriculum",
            ).registration.provider_id
            == "PROVIDER-B",
        ),
        (
            "EDPR6 Future capability requires no registry change",
            registry.resolve(
                capability="future_capability",
            ).registration.provider_id
            == "PROVIDER-A",
        ),
        (
            "EDPR7 Unknown capability blocked",
            expect_error(
                LookupError,
                lambda: registry.resolve(
                    capability="unknown_capability",
                ),
            ),
        ),
        (
            "EDPR8 Duplicate provider ID blocked",
            expect_error(
                ValueError,
                lambda: registry.register(
                    registration=registration_a,
                    provider=provider_a,
                ),
            ),
        ),
        (
            "EDPR9 Unknown provider blocked",
            expect_error(
                KeyError,
                lambda: registry.get(
                    provider_id="UNKNOWN",
                ),
            ),
        ),
        (
            "EDPR10 Wrong registration type blocked",
            expect_error(
                TypeError,
                lambda: registry.register(
                    registration="bad",
                    provider=provider_a,
                ),
            ),
        ),
        (
            "EDPR11 Wrong provider type blocked",
            expect_error(
                TypeError,
                lambda: registry.register(
                    registration=ProviderRegistration(
                        provider_id="BAD",
                        capabilities=("X",),
                    ),
                    provider="bad",
                ),
            ),
        ),
    ]

    ordered = registry.registrations()

    checks.append(
        (
            "EDPR12 Registrations deterministically ordered",
            tuple(
                item.provider_id
                for item in ordered
            )
            == (
                "PROVIDER-DISABLED",
                "PROVIDER-B",
                "PROVIDER-A",
            ),
        )
    )

    registry.unregister(
        provider_id="PROVIDER-A"
    )

    checks.append(
        (
            "EDPR13 Provider unregister works",
            expect_error(
                KeyError,
                lambda: registry.get(
                    provider_id="PROVIDER-A",
                ),
            ),
        )
    )

    for label, passed in checks:
        results.append(passed)

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    # --------------------------------------------------------
    # DATA INDEPENDENCE ARCHITECTURE GUARD
    # --------------------------------------------------------

    source = inspect.getsource(
        EducationalDataProviderRegistry
    ).lower()

    forbidden_tokens = (
        "140",
        "2018",
        "5512",
        "7991",
        "kntt",
        "kết nối tri thức",
        "toán 6",
        "lbg-tuyen",
        ".xlsm",
        ".xlsx",
        "openpyxl",
        "load_workbook",
        "worksheet",
        "textbook-math",
        "yccd-math",
    )

    violations = [
        token
        for token in forbidden_tokens
        if token in source
    ]

    passed = not violations
    results.append(passed)

    print(
        "EDPR14 Registry data-independence guard: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    physical_parameters = {
        "file_path",
        "workbook",
        "worksheet",
        "sheet",
        "json_file",
        "excel_file",
        "database",
        "connection",
    }

    registry_methods = (
        "register",
        "unregister",
        "get",
        "providers_for_capability",
        "resolve",
        "registrations",
    )

    physical_violations = []

    for method_name in registry_methods:
        signature = inspect.signature(
            getattr(
                EducationalDataProviderRegistry,
                method_name,
            )
        )

        found = (
            set(signature.parameters)
            & physical_parameters
        )

        if found:
            physical_violations.append(
                (
                    method_name,
                    sorted(found),
                )
            )

    passed = not physical_violations
    results.append(passed)

    print(
        "EDPR15 Registry hides physical storage: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    future_registry = (
        EducationalDataProviderRegistry()
    )

    future_provider = FakeProvider(
        "FUTURE"
    )

    future_registry.register(
        registration=ProviderRegistration(
            provider_id="FUTURE",
            capabilities=(
                "brand_new_education_data",
            ),
        ),
        provider=future_provider,
    )

    passed = (
        future_registry.resolve(
            capability="brand_new_education_data",
        ).provider
        is future_provider
    )

    results.append(passed)

    print(
        "EDPR16 New data capability needs no registry modification: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if violations:
        print(
            "DATA HARD-CODE VIOLATIONS:",
            violations,
        )

    if physical_violations:
        print(
            "PHYSICAL STORAGE VIOLATIONS:",
            physical_violations,
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - EDUCATIONAL DATA "
            "PROVIDER REGISTRY VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - EDUCATIONAL DATA "
            "PROVIDER REGISTRY VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
