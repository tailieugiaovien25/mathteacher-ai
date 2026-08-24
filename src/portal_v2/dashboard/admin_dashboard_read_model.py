from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final


DASHBOARD_STATUS_DRAFT: Final = "DRAFT"
DASHBOARD_STATUS_PENDING: Final = "PENDING"
DASHBOARD_STATUS_VERIFIED: Final = "VERIFIED"
DASHBOARD_STATUS_PUBLISHED: Final = "PUBLISHED"

DASHBOARD_STATUSES: Final = (
    DASHBOARD_STATUS_DRAFT,
    DASHBOARD_STATUS_PENDING,
    DASHBOARD_STATUS_VERIFIED,
    DASHBOARD_STATUS_PUBLISHED,
)


@dataclass(frozen=True)
class AdminDashboardStatusCounts:
    draft: int
    pending: int
    verified: int
    published: int

    def __post_init__(self) -> None:
        for field_name in (
            "draft",
            "pending",
            "verified",
            "published",
        ):
            value = getattr(self, field_name)

            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(
                    f"{field_name} must be int"
                )

            if value < 0:
                raise ValueError(
                    f"{field_name} must be >= 0"
                )

    @property
    def total(self) -> int:
        return (
            self.draft
            + self.pending
            + self.verified
            + self.published
        )


@dataclass(frozen=True)
class AdminDashboardActivity:
    activity_id: str
    record_id: str
    action: str
    actor_id: str
    occurred_at: datetime
    summary: str

    def __post_init__(self) -> None:
        for field_name in (
            "activity_id",
            "record_id",
            "action",
            "actor_id",
            "summary",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be empty"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if not isinstance(
            self.occurred_at,
            datetime,
        ):
            raise TypeError(
                "occurred_at must be datetime"
            )


@dataclass(frozen=True)
class AdminDashboardReadModel:
    status_counts: AdminDashboardStatusCounts
    recent_activity: tuple[AdminDashboardActivity, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(
            self.status_counts,
            AdminDashboardStatusCounts,
        ):
            raise TypeError(
                "status_counts must be AdminDashboardStatusCounts"
            )

        if not isinstance(
            self.recent_activity,
            tuple,
        ):
            raise TypeError(
                "recent_activity must be tuple"
            )

        if not all(
            isinstance(
                item,
                AdminDashboardActivity,
            )
            for item in self.recent_activity
        ):
            raise TypeError(
                "recent_activity items must be AdminDashboardActivity"
            )

        if not isinstance(
            self.generated_at,
            datetime,
        ):
            raise TypeError(
                "generated_at must be datetime"
            )
