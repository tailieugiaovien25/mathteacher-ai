from dataclasses import dataclass

from curriculum_v2.providers.contracts import (
    ProviderRegistration,
)
from curriculum_v2.providers.educational_data_provider import (
    EducationalDataProvider,
)


@dataclass(frozen=True)
class RegisteredEducationalDataProvider:
    """One provider instance bound to its registration metadata."""

    registration: ProviderRegistration
    provider: EducationalDataProvider

    def __post_init__(self) -> None:
        if not isinstance(
            self.registration,
            ProviderRegistration,
        ):
            raise TypeError(
                "registration must be ProviderRegistration"
            )

        if not isinstance(
            self.provider,
            EducationalDataProvider,
        ):
            raise TypeError(
                "provider must implement EducationalDataProvider"
            )


class EducationalDataProviderRegistry:
    """
    Runtime registry for educational data providers.

    The registry is provider-neutral and data-neutral.
    It resolves providers only through declared capabilities,
    enabled state, priority, and deterministic provider identity.
    """

    def __init__(self) -> None:
        self._providers: dict[
            str,
            RegisteredEducationalDataProvider,
        ] = {}

    def register(
        self,
        *,
        registration: ProviderRegistration,
        provider: EducationalDataProvider,
    ) -> None:
        entry = RegisteredEducationalDataProvider(
            registration=registration,
            provider=provider,
        )

        provider_id = registration.provider_id

        if provider_id in self._providers:
            raise ValueError(
                f"provider already registered: {provider_id}"
            )

        self._providers[
            provider_id
        ] = entry

    def unregister(
        self,
        *,
        provider_id: str,
    ) -> None:
        provider_id = self._required_text(
            provider_id,
            "provider_id",
        )

        if provider_id not in self._providers:
            raise KeyError(
                f"provider not registered: {provider_id}"
            )

        del self._providers[
            provider_id
        ]

    def get(
        self,
        *,
        provider_id: str,
    ) -> RegisteredEducationalDataProvider:
        provider_id = self._required_text(
            provider_id,
            "provider_id",
        )

        try:
            return self._providers[
                provider_id
            ]
        except KeyError as error:
            raise KeyError(
                f"provider not registered: {provider_id}"
            ) from error

    def providers_for_capability(
        self,
        *,
        capability: str,
    ) -> tuple[
        RegisteredEducationalDataProvider,
        ...,
    ]:
        capability = self._required_text(
            capability,
            "capability",
        )

        eligible = [
            entry
            for entry in self._providers.values()
            if entry.registration.supports(
                capability
            )
        ]

        eligible.sort(
            key=lambda entry: (
                entry.registration.priority,
                entry.registration.provider_id,
            )
        )

        return tuple(
            eligible
        )

    def resolve(
        self,
        *,
        capability: str,
    ) -> RegisteredEducationalDataProvider:
        candidates = (
            self.providers_for_capability(
                capability=capability,
            )
        )

        if not candidates:
            raise LookupError(
                "no enabled provider supports capability: "
                f"{capability}"
            )

        return candidates[0]

    def registrations(
        self,
    ) -> tuple[
        ProviderRegistration,
        ...,
    ]:
        ordered = sorted(
            (
                entry.registration
                for entry in self._providers.values()
            ),
            key=lambda registration: (
                registration.priority,
                registration.provider_id,
            ),
        )

        return tuple(
            ordered
        )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
