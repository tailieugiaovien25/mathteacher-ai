from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from portal_v2.dashboard.admin_dashboard_read_model import (
    AdminDashboardActivity,
    AdminDashboardReadModel,
    AdminDashboardStatusCounts,
)


class AdminDashboardQuerySource(ABC):
    """
    Stable source contract for dashboard aggregation.

    Implementations may query repositories, providers, or other
    persistence-backed services, but the dashboard service remains
    storage-neutral.
    """

    @abstractmethod
    def status_counts(
        self,
    ) -> AdminDashboardStatusCounts:
        raise NotImplementedError

    @abstractmethod
    def recent_activity(
        self,
        *,
        limit: int,
    ) -> tuple[AdminDashboardActivity, ...]:
        raise NotImplementedError


class AdminDashboardQueryService:
    """
    Application service that assembles the canonical dashboard read model.
    """

    def __init__(
        self,
        *,
        source: AdminDashboardQuerySource,
        clock,
    ) -> None:
        if not isinstance(
            source,
            AdminDashboardQuerySource,
        ):
            raise TypeError(
                "source must implement AdminDashboardQuerySource"
            )

        if not callable(clock):
            raise TypeError(
                "clock must be callable"
            )

        self._source = source
        self._clock = clock

    def build_read_model(
        self,
        *,
        activity_limit: int = 10,
    ) -> AdminDashboardReadModel:
        if isinstance(
            activity_limit,
            bool,
        ) or not isinstance(
            activity_limit,
            int,
        ):
            raise TypeError(
                "activity_limit must be int"
            )

        if activity_limit <= 0:
            raise ValueError(
                "activity_limit must be > 0"
            )

        counts = self._source.status_counts()

        if not isinstance(
            counts,
            AdminDashboardStatusCounts,
        ):
            raise TypeError(
                "source returned invalid status counts"
            )

        activity = self._source.recent_activity(
            limit=activity_limit,
        )

        if not isinstance(
            activity,
            tuple,
        ):
            raise TypeError(
                "source returned non-tuple activity"
            )

        if not all(
            isinstance(
                item,
                AdminDashboardActivity,
            )
            for item in activity
        ):
            raise TypeError(
                "source returned invalid activity item"
            )

        generated_at = self._clock()

        if not isinstance(
            generated_at,
            datetime,
        ):
            raise TypeError(
                "clock must return datetime"
            )

        return AdminDashboardReadModel(
            status_counts=counts,
            recent_activity=activity,
            generated_at=generated_at,
        )
