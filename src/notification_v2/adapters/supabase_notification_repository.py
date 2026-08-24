from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from notification_v2.models import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from notification_v2.repositories import (
    NotificationRepository,
)


class SupabaseNotificationRepository(
    NotificationRepository
):
    TABLE_NAME = "notifications"

    def __init__(
        self,
        client: Any,
        owner_id: str,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        self._client = client
        self._owner_id = self._required_text(
            owner_id,
            "owner_id",
        )

    def save(
        self,
        *,
        notification: Notification,
    ) -> Notification:
        if not isinstance(
            notification,
            Notification,
        ):
            raise TypeError(
                "notification must be Notification"
            )

        self._assert_owner(
            notification.owner_id
        )

        row = self._to_row(
            notification
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .upsert(
                row,
                on_conflict="notification_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        return (
            self._from_row(rows[0])
            if rows
            else notification
        )

    def get(
        self,
        *,
        notification_id: str,
        owner_id: str,
    ) -> Notification | None:
        self._assert_owner(
            owner_id
        )

        normalized_id = self._required_text(
            notification_id,
            "notification_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "notification_id",
                normalized_id,
            )
            .eq(
                "owner_id",
                self._owner_id,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return None

        return self._from_row(
            rows[0]
        )

    def list_for_owner(
        self,
        *,
        owner_id: str,
        status: NotificationStatus | None = None,
        limit: int | None = None,
    ) -> tuple[Notification, ...]:
        self._assert_owner(
            owner_id
        )

        self._validate_status(
            status
        )

        if limit is not None:
            if not isinstance(limit, int):
                raise TypeError(
                    "limit must be int or None"
                )

            if limit <= 0:
                raise ValueError(
                    "limit must be greater than zero"
                )

        query = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "owner_id",
                self._owner_id,
            )
        )

        if status is not None:
            query = query.eq(
                "status",
                status.value,
            )

        query = query.order(
            "created_at",
            desc=True,
        )

        if limit is not None:
            query = query.limit(
                limit
            )

        response = query.execute()

        return tuple(
            self._from_row(row)
            for row in self._response_rows(
                response
            )
        )

    def count_unread(
        self,
        *,
        owner_id: str,
    ) -> int:
        self._assert_owner(
            owner_id
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("notification_id")
            .eq(
                "owner_id",
                self._owner_id,
            )
            .eq(
                "status",
                NotificationStatus.UNREAD.value,
            )
            .execute()
        )

        return len(
            self._response_rows(
                response
            )
        )

    def mark_read(
        self,
        *,
        notification_id: str,
        owner_id: str,
        read_at: datetime | None = None,
    ) -> Notification | None:
        self._assert_owner(
            owner_id
        )

        normalized_id = self._required_text(
            notification_id,
            "notification_id",
        )

        timestamp = self._read_timestamp(
            read_at
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .update(
                {
                    "status":
                        NotificationStatus.READ.value,
                    "read_at":
                        timestamp.isoformat(),
                    "updated_at":
                        timestamp.isoformat(),
                }
            )
            .eq(
                "notification_id",
                normalized_id,
            )
            .eq(
                "owner_id",
                self._owner_id,
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return None

        return self._from_row(
            rows[0]
        )

    def mark_all_read(
        self,
        *,
        owner_id: str,
        read_at: datetime | None = None,
    ) -> int:
        self._assert_owner(
            owner_id
        )

        timestamp = self._read_timestamp(
            read_at
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .update(
                {
                    "status":
                        NotificationStatus.READ.value,
                    "read_at":
                        timestamp.isoformat(),
                    "updated_at":
                        timestamp.isoformat(),
                }
            )
            .eq(
                "owner_id",
                self._owner_id,
            )
            .eq(
                "status",
                NotificationStatus.UNREAD.value,
            )
            .execute()
        )

        return len(
            self._response_rows(
                response
            )
        )

    @staticmethod
    def _to_row(
        notification: Notification,
    ) -> dict[str, Any]:
        return {
            "notification_id":
                notification.notification_id,
            "owner_id":
                notification.owner_id,
            "type":
                notification.type.value,
            "priority":
                notification.priority.value,
            "title":
                notification.title,
            "message":
                notification.message,
            "source_module":
                notification.source_module,
            "source_id":
                notification.source_id,
            "action_ref":
                notification.action_ref,
            "status":
                notification.status.value,
            "created_at":
                notification.created_at.isoformat(),
            "read_at": (
                None
                if notification.read_at is None
                else notification.read_at.isoformat()
            ),
        }

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> Notification:
        return Notification(
            notification_id=str(
                row["notification_id"]
            ),
            owner_id=str(
                row["owner_id"]
            ),
            type=NotificationType(
                str(row["type"])
            ),
            priority=NotificationPriority(
                str(row["priority"])
            ),
            title=str(
                row["title"]
            ),
            message=str(
                row["message"]
            ),
            source_module=str(
                row["source_module"]
            ),
            source_id=(
                None
                if row.get("source_id") is None
                else str(row["source_id"])
            ),
            action_ref=(
                None
                if row.get("action_ref") is None
                else str(row["action_ref"])
            ),
            status=NotificationStatus(
                str(row["status"])
            ),
            created_at=(
                SupabaseNotificationRepository
                ._datetime_from_value(
                    row["created_at"]
                )
            ),
            read_at=(
                None
                if row.get("read_at") is None
                else (
                    SupabaseNotificationRepository
                    ._datetime_from_value(
                        row["read_at"]
                    )
                )
            ),
        )

    def _assert_owner(
        self,
        owner_id: str,
    ) -> None:
        normalized = self._required_text(
            owner_id,
            "owner_id",
        )

        if normalized != self._owner_id:
            raise ValueError(
                "owner_id does not match "
                "authenticated owner"
            )

    @staticmethod
    def _read_timestamp(
        value: datetime | None,
    ) -> datetime:
        if value is None:
            return datetime.now(
                timezone.utc
            )

        if not isinstance(
            value,
            datetime,
        ):
            raise TypeError(
                "read_at must be datetime or None"
            )

        return value

    @staticmethod
    def _datetime_from_value(
        value: Any,
    ) -> datetime:
        if isinstance(
            value,
            datetime,
        ):
            return value

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "datetime value must be "
                "datetime or str"
            )

        normalized = value.strip()

        if normalized.endswith("Z"):
            normalized = (
                normalized[:-1]
                + "+00:00"
            )

        return datetime.fromisoformat(
            normalized
        )

    @staticmethod
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        data = getattr(
            response,
            "data",
            None,
        )

        if not isinstance(
            data,
            list,
        ):
            return []

        return [
            row
            for row in data
            if isinstance(
                row,
                dict,
            )
        ]

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
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _validate_status(
        status: NotificationStatus | None,
    ) -> None:
        if (
            status is not None
            and not isinstance(
                status,
                NotificationStatus,
            )
        ):
            raise TypeError(
                "status must be "
                "NotificationStatus or None"
            )
