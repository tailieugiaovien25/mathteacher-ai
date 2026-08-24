from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class NotificationType(str, Enum):
    DATA_CHANGED = "DATA_CHANGED"
    ASSIGNMENT_CHANGED = "ASSIGNMENT_CHANGED"
    SCHEDULE_CHANGED = "SCHEDULE_CHANGED"
    PROCESS_COMPLETED = "PROCESS_COMPLETED"
    SYSTEM = "SYSTEM"


class NotificationPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class NotificationStatus(str, Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class Notification:
    notification_id: str
    owner_id: str

    type: NotificationType
    title: str
    message: str

    source_module: str

    priority: NotificationPriority = (
        NotificationPriority.NORMAL
    )

    source_id: str | None = None
    action_ref: str | None = None

    status: NotificationStatus = (
        NotificationStatus.UNREAD
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    read_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "notification_id",
            self._required_text(
                self.notification_id,
                "notification_id",
            ),
        )

        object.__setattr__(
            self,
            "owner_id",
            self._required_text(
                self.owner_id,
                "owner_id",
            ),
        )

        object.__setattr__(
            self,
            "title",
            self._required_text(
                self.title,
                "title",
            ),
        )

        object.__setattr__(
            self,
            "message",
            self._required_text(
                self.message,
                "message",
            ),
        )

        object.__setattr__(
            self,
            "source_module",
            self._required_text(
                self.source_module,
                "source_module",
            ),
        )

        object.__setattr__(
            self,
            "source_id",
            self._optional_text(
                self.source_id,
                "source_id",
            ),
        )

        object.__setattr__(
            self,
            "action_ref",
            self._optional_text(
                self.action_ref,
                "action_ref",
            ),
        )

        if not isinstance(
            self.type,
            NotificationType,
        ):
            raise TypeError(
                "type must be NotificationType"
            )

        if not isinstance(
            self.priority,
            NotificationPriority,
        ):
            raise TypeError(
                "priority must be NotificationPriority"
            )

        if not isinstance(
            self.status,
            NotificationStatus,
        ):
            raise TypeError(
                "status must be NotificationStatus"
            )

        if not isinstance(
            self.created_at,
            datetime,
        ):
            raise TypeError(
                "created_at must be datetime"
            )

        if (
            self.read_at is not None
            and not isinstance(
                self.read_at,
                datetime,
            )
        ):
            raise TypeError(
                "read_at must be datetime or None"
            )

        if (
            self.status is NotificationStatus.READ
            and self.read_at is None
        ):
            raise ValueError(
                "READ notification requires read_at"
            )

        if (
            self.status is NotificationStatus.UNREAD
            and self.read_at is not None
        ):
            raise ValueError(
                "UNREAD notification must not have read_at"
            )

    def mark_read(
        self,
        *,
        read_at: datetime | None = None,
    ) -> Notification:
        timestamp = (
            datetime.now(timezone.utc)
            if read_at is None
            else read_at
        )

        return Notification(
            notification_id=self.notification_id,
            owner_id=self.owner_id,
            type=self.type,
            priority=self.priority,
            title=self.title,
            message=self.message,
            source_module=self.source_module,
            source_id=self.source_id,
            action_ref=self.action_ref,
            status=NotificationStatus.READ,
            created_at=self.created_at,
            read_at=timestamp,
        )

    def archive(self) -> Notification:
        return Notification(
            notification_id=self.notification_id,
            owner_id=self.owner_id,
            type=self.type,
            priority=self.priority,
            title=self.title,
            message=self.message,
            source_module=self.source_module,
            source_id=self.source_id,
            action_ref=self.action_ref,
            status=NotificationStatus.ARCHIVED,
            created_at=self.created_at,
            read_at=self.read_at,
        )

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
    def _optional_text(
        value: str | None,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be str or None"
            )

        normalized = value.strip()

        return normalized or None
