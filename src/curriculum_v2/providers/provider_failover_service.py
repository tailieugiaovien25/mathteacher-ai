from curriculum_v2.providers.contracts import (
    EducationalDataQuery,
    EducationalDataResult,
)
from curriculum_v2.providers.educational_data_provider_registry import (
    EducationalDataProviderRegistry,
)


class EducationalDataProviderUnavailableError(RuntimeError):
    """Signal that a provider cannot serve a valid request at runtime."""


class EducationalDataProviderFailoverService:
    """Execute a provider-neutral query with deterministic failover."""

    def __init__(self, registry: EducationalDataProviderRegistry) -> None:
        if not isinstance(registry, EducationalDataProviderRegistry):
            raise TypeError(
                "registry must be EducationalDataProviderRegistry"
            )
        self._registry = registry

    def query(
        self,
        query: EducationalDataQuery,
    ) -> EducationalDataResult:
        if not isinstance(query, EducationalDataQuery):
            raise TypeError("query must be EducationalDataQuery")

        candidates = self._registry.providers_for_capability(
            capability=query.capability
        )
        if not candidates:
            raise LookupError(
                "no enabled provider supports capability: "
                f"{query.capability}"
            )

        unavailable_provider_ids = []
        for candidate in candidates:
            try:
                return candidate.provider.query(query)
            except EducationalDataProviderUnavailableError:
                unavailable_provider_ids.append(
                    candidate.registration.provider_id
                )

        attempted = ", ".join(unavailable_provider_ids)
        raise EducationalDataProviderUnavailableError(
            "all eligible educational data providers are unavailable: "
            f"{attempted}"
        )
