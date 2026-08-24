from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from notification_v2.models import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from notification_v2.repositories import (
    NotificationRepository,
)


class NotificationService:
    def __init__(
        self,
        *,
        repository: NotificationRepository,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if repository is None:
            raise ValueError(
                "repository must not be None"
            )

        self._repository = repository

        self._id_factory = (
            id_factory
            if id_factory is not None
            else lambda: str(uuid4())
        )

        self._clock = (
            clock
            if clock is not None
            else lambda: datetime.now(
                timezone.utc
            )
        )

    def publish(
        self,
        *,
        owner_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        source_module: str,
        priority: NotificationPriority = (
            NotificationPriority.NORMAL
        ),
        source_id: str | None = None,
        action_ref: str | None = None,
    ) -> Notification:
        notification = Notification(
            notification_id=(
                self._id_factory()
            ),
            owner_id=owner_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            source_module=source_module,
            source_id=source_id,
            action_ref=action_ref,
            status=NotificationStatus.UNREAD,
            created_at=self._clock(),
        )

        return self._repository.save(
            notification=notification
        )

    def list_for_owner(
        self,
        *,
        owner_id: str,
        status: NotificationStatus | None = None,
        limit: int | None = None,
    ) -> tuple[Notification, ...]:
        return self._repository.list_for_owner(
            owner_id=owner_id,
            status=status,
            limit=limit,
        )

    def count_unread(
        self,
        *,
        owner_id: str,
    ) -> int:
        return self._repository.count_unread(
            owner_id=owner_id
        )

    def mark_read(
        self,
        *,
        notification_id: str,
        owner_id: str,
    ) -> Notification | None:
        return self._repository.mark_read(
            notification_id=notification_id,
            owner_id=owner_id,
            read_at=self._clock(),
        )

    def mark_all_read(
        self,
        *,
        owner_id: str,
    ) -> int:
        return self._repository.mark_all_read(
            owner_id=owner_id,
            read_at=self._clock(),
        )
