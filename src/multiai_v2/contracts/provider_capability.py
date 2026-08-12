from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapability:
    """
    Canonical description of one capability exposed by an AI provider.

    The capability identity is independent from any concrete provider,
    vendor, SDK, or model implementation.
    """

    capability_id: str
    version: str

    def __post_init__(self) -> None:
        capability_id = self.capability_id.strip()
        version = self.version.strip()

        if not capability_id:
            raise ValueError(
                "capability_id must not be empty"
            )

        if not version:
            raise ValueError(
                "version must not be empty"
            )

        object.__setattr__(
            self,
            "capability_id",
            capability_id,
        )

        object.__setattr__(
            self,
            "version",
            version,
        )