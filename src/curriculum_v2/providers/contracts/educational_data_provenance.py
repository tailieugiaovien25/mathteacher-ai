from dataclasses import dataclass


@dataclass(frozen=True)
class EducationalDataProvenance:
    """Provider-neutral provenance for educational data."""

    source_id: str
    authority_type: str

    source_version: str | None = None
    verified_copy_id: str | None = None

    status: str = "CANDIDATE"

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "authority_type",
            "status",
        ):
            object.__setattr__(
                self,
                field_name,
                self._required_text(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                ),
            )

        object.__setattr__(
            self,
            "status",
            self.status.upper(),
        )

        for field_name in (
            "source_version",
            "verified_copy_id",
        ):
            value = getattr(
                self,
                field_name,
            )

            if value is None:
                continue

            object.__setattr__(
                self,
                field_name,
                self._required_text(
                    value,
                    field_name,
                ),
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
