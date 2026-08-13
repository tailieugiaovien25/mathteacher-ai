from dataclasses import dataclass
from typing import Any

from curriculum_v2.providers.contracts.educational_data_provenance import (
    EducationalDataProvenance,
)
from curriculum_v2.providers.contracts.educational_data_version import (
    EducationalDataVersion,
)


@dataclass(frozen=True)
class EducationalDataResult:
    """Provider-neutral result envelope."""

    capability: str

    data: tuple[Any, ...]

    provenance: EducationalDataProvenance
    version: EducationalDataVersion

    status: str = "OK"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "capability",
            self._required_text(
                self.capability,
                "capability",
            ),
        )

        if not isinstance(
            self.data,
            tuple,
        ):
            raise TypeError(
                "data must be a tuple"
            )

        if not isinstance(
            self.provenance,
            EducationalDataProvenance,
        ):
            raise TypeError(
                "provenance must be "
                "EducationalDataProvenance"
            )

        if not isinstance(
            self.version,
            EducationalDataVersion,
        ):
            raise TypeError(
                "version must be "
                "EducationalDataVersion"
            )

        object.__setattr__(
            self,
            "status",
            self._required_text(
                self.status,
                "status",
            ).upper(),
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
