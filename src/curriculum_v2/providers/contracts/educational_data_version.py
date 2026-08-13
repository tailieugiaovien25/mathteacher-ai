from dataclasses import dataclass


@dataclass(frozen=True)
class EducationalDataVersion:
    """Version identity for replaceable educational data."""

    version_id: str

    effective_from: str | None = None
    effective_to: str | None = None

    supersedes_version_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "version_id",
            self._required_text(
                self.version_id,
                "version_id",
            ),
        )

        for field_name in (
            "effective_from",
            "effective_to",
            "supersedes_version_id",
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
