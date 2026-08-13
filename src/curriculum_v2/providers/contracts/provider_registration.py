from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class ProviderRegistration:
    """
    Provider-neutral registration contract.

    The registration describes provider identity and declared
    capabilities without exposing physical data-source details
    or concrete educational content.
    """

    provider_id: str
    capabilities: tuple[str, ...]

    priority: int = 100
    enabled: bool = True

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provider_id",
            self._required_text(
                self.provider_id,
                "provider_id",
            ),
        )

        if not isinstance(
            self.capabilities,
            tuple,
        ):
            raise TypeError(
                "capabilities must be a tuple"
            )

        normalized_capabilities = []

        for capability in self.capabilities:
            normalized = self._required_text(
                capability,
                "capability",
            )

            if normalized not in normalized_capabilities:
                normalized_capabilities.append(
                    normalized
                )

        if not normalized_capabilities:
            raise ValueError(
                "capabilities must not be empty"
            )

        object.__setattr__(
            self,
            "capabilities",
            tuple(normalized_capabilities),
        )

        if (
            isinstance(self.priority, bool)
            or not isinstance(self.priority, int)
        ):
            raise TypeError(
                "priority must be an integer"
            )

        if self.priority < 0:
            raise ValueError(
                "priority must not be negative"
            )

        if not isinstance(
            self.enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be a boolean"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping"
            )

        metadata_copy = dict(
            self.metadata
        )

        for key in metadata_copy:
            if not isinstance(key, str):
                raise TypeError(
                    "metadata keys must be strings"
                )

            if not key.strip():
                raise ValueError(
                    "metadata keys must not be empty"
                )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                metadata_copy
            ),
        )

    def supports(
        self,
        capability: str,
    ) -> bool:
        normalized = self._required_text(
            capability,
            "capability",
        )

        return (
            self.enabled
            and normalized in self.capabilities
        )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
