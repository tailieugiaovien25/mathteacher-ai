from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class AssignmentRoundStatus(
    str,
    Enum,
):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


def _required_text(
    value: str,
    field_name: str,
    maximum: int = 250,
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

    if len(normalized) > maximum:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum} characters"
        )

    return normalized


@dataclass(frozen=True)
class AssignmentRound:
    round_id: str
    academic_year: str
    round_number: int
    effective_from: date
    status: AssignmentRoundStatus = (
        AssignmentRoundStatus.ACTIVE
    )
    label: str | None = None

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "round_id",
            _required_text(
                self.round_id,
                "round_id",
                120,
            ),
        )

        object.__setattr__(
            self,
            "academic_year",
            _required_text(
                self.academic_year,
                "academic_year",
                30,
            ),
        )

        if (
            not isinstance(
                self.round_number,
                int,
            )
            or isinstance(
                self.round_number,
                bool,
            )
        ):
            raise TypeError(
                "round_number must be int"
            )

        if self.round_number < 1:
            raise ValueError(
                "round_number must be at least 1"
            )

        if not isinstance(
            self.effective_from,
            date,
        ):
            raise TypeError(
                "effective_from must be a date"
            )

        if not isinstance(
            self.status,
            AssignmentRoundStatus,
        ):
            raise TypeError(
                "status must be AssignmentRoundStatus"
            )

        if self.label is None:
            normalized_label = (
                f"L\u1ea7n {self.round_number}"
            )
        else:
            normalized_label = _required_text(
                self.label,
                "label",
                100,
            )

        object.__setattr__(
            self,
            "label",
            normalized_label,
        )
