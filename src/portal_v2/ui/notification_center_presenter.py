from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from notification_v2.models import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


@dataclass(frozen=True)
class NotificationCenterItem:
    notification_id: str
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    status: NotificationStatus
    created_at: datetime
    action_ref: str | None
    is_unread: bool


@dataclass(frozen=True)
class NotificationCenterView:
    unread_count: int
    items: tuple[NotificationCenterItem, ...]

    @property
    def has_notifications(self) -> bool:
        return bool(self.items)

    @property
    def has_unread(self) -> bool:
        return self.unread_count > 0


def build_notification_center_view(
    *,
    notifications: tuple[Notification, ...],
    unread_count: int,
) -> NotificationCenterView:
    if unread_count < 0:
        raise ValueError(
            "unread_count must not be negative"
        )

    items = tuple(
        NotificationCenterItem(
            notification_id=notification.notification_id,
            title=notification.title,
            message=notification.message,
            type=notification.type,
            priority=notification.priority,
            status=notification.status,
            created_at=notification.created_at,
            action_ref=notification.action_ref,
            is_unread=(
                notification.status
                is NotificationStatus.UNREAD
            ),
        )
        for notification in notifications
    )

    return NotificationCenterView(
        unread_count=unread_count,
        items=items,
    )
