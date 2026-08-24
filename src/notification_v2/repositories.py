from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from notification_v2.models import (
    Notification,
    NotificationStatus,
)


class NotificationRepository(ABC):
    @abstractmethod
    def save(
        self,
        *,
        notification: Notification,
    ) -> Notification:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        notification_id: str,
        owner_id: str,
    ) -> Notification | None:
        raise NotImplementedError

    @abstractmethod
    def list_for_owner(
        self,
        *,
        owner_id: str,
        status: NotificationStatus | None = None,
        limit: int | None = None,
    ) -> tuple[Notification, ...]:
        raise NotImplementedError

    @abstractmethod
    def count_unread(
        self,
        *,
        owner_id: str,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def mark_read(
        self,
        *,
        notification_id: str,
        owner_id: str,
        read_at: datetime | None = None,
    ) -> Notification | None:
        raise NotImplementedError

    @abstractmethod
    def mark_all_read(
        self,
        *,
        owner_id: str,
        read_at: datetime | None = None,
    ) -> int:
        raise NotImplementedError
