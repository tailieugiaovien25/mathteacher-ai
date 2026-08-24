from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from curriculum_v2.governance.trusted_admin_data_repository import (
    TrustedAdministrativeDataRepository,
)
from portal_v2.dashboard.admin_dashboard_query_service import (
    AdminDashboardQuerySource,
)
from portal_v2.dashboard.admin_dashboard_read_model import (
    AdminDashboardActivity,
    AdminDashboardStatusCounts,
)


class TrustedAdminRepositoryDashboardQuerySource(
    AdminDashboardQuerySource
):
    """
    Read-only dashboard adapter over the trusted administrative repository.

    The adapter understands logical governance record attributes only.
    It contains no physical persistence dependency.
    """

    def __init__(
        self,
        *,
        repository: TrustedAdministrativeDataRepository,
    ) -> None:
        if not isinstance(
            repository,
            TrustedAdministrativeDataRepository,
        ):
            raise TypeError(
                "repository must implement "
                "TrustedAdministrativeDataRepository"
            )

        self._repository = repository

    def status_counts(
        self,
    ) -> AdminDashboardStatusCounts:
        counts = {
            "DRAFT": 0,
            "PENDING": 0,
            "VERIFIED": 0,
            "PUBLISHED": 0,
        }

        for record in self._repository.list_records():
            status = self._record_status(
                record
            )

            if status in counts:
                counts[status] += 1

        return AdminDashboardStatusCounts(
            draft=counts["DRAFT"],
            pending=counts["PENDING"],
            verified=counts["VERIFIED"],
            published=counts["PUBLISHED"],
        )

    def recent_activity(
        self,
        *,
        limit: int,
    ) -> tuple[AdminDashboardActivity, ...]:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError(
                "limit must be int"
            )

        if limit <= 0:
            raise ValueError(
                "limit must be > 0"
            )

        activities: list[AdminDashboardActivity] = []

        for record in self._repository.list_records():
            record_id = self._record_id(
                record
            )

            for index, event in enumerate(
                self._audit_events(
                    record
                )
            ):
                activity = self._activity_from_event(
                    record_id=record_id,
                    index=index,
                    event=event,
                )

                if activity is not None:
                    activities.append(
                        activity
                    )

        activities.sort(
            key=lambda item: (
                item.occurred_at,
                item.activity_id,
            ),
            reverse=True,
        )

        return tuple(
            activities[:limit]
        )

    @classmethod
    def _record_status(
        cls,
        record: Any,
    ) -> str:
        value = cls._read_value(
            record,
            "state",
            "status",
        )

        if isinstance(value, Enum):
            value = value.value

        if not isinstance(value, str):
            return ""

        return value.strip().upper()

    @classmethod
    def _record_id(
        cls,
        record: Any,
    ) -> str:
        value = cls._read_value(
            record,
            "submission_id",
            "record_id",
            "id",
        )

        if not isinstance(value, str):
            return ""

        return value.strip()

    @classmethod
    def _audit_events(
        cls,
        record: Any,
    ) -> tuple[Any, ...]:
        value = cls._read_value(
            record,
            "audit_trail",
        )

        if not isinstance(
            value,
            (tuple, list),
        ):
            return ()

        return tuple(value)

    @classmethod
    def _activity_from_event(
        cls,
        *,
        record_id: str,
        index: int,
        event: Any,
    ) -> AdminDashboardActivity | None:
        action = cls._text_value(
            event,
            "action",
            "event_type",
            "transition",
        )
        actor_id = cls._text_value(
            event,
            "actor_id",
            "performed_by",
            "user_id",
        )
        occurred_at = cls._datetime_value(
            event,
            "occurred_at",
            "created_at",
            "timestamp",
        )
        summary = cls._text_value(
            event,
            "summary",
            "reason",
            "description",
        )

        if (
            not record_id
            or not action
            or not actor_id
            or occurred_at is None
        ):
            return None

        if not summary:
            summary = action

        activity_id = cls._text_value(
            event,
            "activity_id",
            "event_id",
            "audit_id",
        )

        if not activity_id:
            activity_id = (
                f"{record_id}:"
                f"{occurred_at.isoformat()}:"
                f"{index}"
            )

        return AdminDashboardActivity(
            activity_id=activity_id,
            record_id=record_id,
            action=action,
            actor_id=actor_id,
            occurred_at=occurred_at,
            summary=summary,
        )

    @classmethod
    def _text_value(
        cls,
        value: Any,
        *names: str,
    ) -> str:
        raw = cls._read_value(
            value,
            *names,
        )

        if isinstance(raw, Enum):
            raw = raw.value

        if not isinstance(raw, str):
            return ""

        return raw.strip()

    @classmethod
    def _datetime_value(
        cls,
        value: Any,
        *names: str,
    ) -> datetime | None:
        raw = cls._read_value(
            value,
            *names,
        )

        if isinstance(raw, datetime):
            return raw

        if isinstance(raw, str):
            normalized = raw.strip()

            if normalized:
                try:
                    return datetime.fromisoformat(
                        normalized.replace(
                            "Z",
                            "+00:00",
                        )
                    )
                except ValueError:
                    return None

        return None

    @staticmethod
    def _read_value(
        value: Any,
        *names: str,
    ) -> Any:
        for name in names:
            if isinstance(
                value,
                Mapping,
            ):
                if name in value:
                    return value[name]
            elif hasattr(
                value,
                name,
            ):
                return getattr(
                    value,
                    name,
                )

        return None
