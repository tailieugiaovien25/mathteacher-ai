from datetime import datetime, timezone

from notification_v2.models import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from notification_v2.services import (
    NotificationService,
)


class FakeNotificationRepository:
    def __init__(self):
        self.rows = {}

    def save(
        self,
        *,
        notification,
    ):
        self.rows[
            notification.notification_id
        ] = notification

        return notification

    def get(
        self,
        *,
        notification_id,
        owner_id,
    ):
        item = self.rows.get(
            notification_id
        )

        if (
            item is None
            or item.owner_id != owner_id
        ):
            return None

        return item

    def list_for_owner(
        self,
        *,
        owner_id,
        status=None,
        limit=None,
    ):
        items = [
            item
            for item in self.rows.values()
            if (
                item.owner_id == owner_id
                and (
                    status is None
                    or item.status is status
                )
            )
        ]

        items.sort(
            key=lambda item: item.created_at,
            reverse=True,
        )

        if limit is not None:
            items = items[:limit]

        return tuple(items)

    def count_unread(
        self,
        *,
        owner_id,
    ):
        return sum(
            1
            for item in self.rows.values()
            if (
                item.owner_id == owner_id
                and item.status
                is NotificationStatus.UNREAD
            )
        )

    def mark_read(
        self,
        *,
        notification_id,
        owner_id,
        read_at=None,
    ):
        item = self.get(
            notification_id=notification_id,
            owner_id=owner_id,
        )

        if item is None:
            return None

        updated = item.mark_read(
            read_at=read_at
        )

        self.rows[
            notification_id
        ] = updated

        return updated

    def mark_all_read(
        self,
        *,
        owner_id,
        read_at=None,
    ):
        updated_count = 0

        for notification_id, item in tuple(
            self.rows.items()
        ):
            if (
                item.owner_id == owner_id
                and item.status
                is NotificationStatus.UNREAD
            ):
                self.rows[
                    notification_id
                ] = item.mark_read(
                    read_at=read_at
                )

                updated_count += 1

        return updated_count


_FIXED_TIME = datetime(
    2026,
    8,
    17,
    10,
    0,
    tzinfo=timezone.utc,
)


def build_service():
    repository = (
        FakeNotificationRepository()
    )

    service = NotificationService(
        repository=repository,
        id_factory=lambda: "notification-001",
        clock=lambda: _FIXED_TIME,
    )

    return service, repository


def test_publish_creates_unread_notification():
    service, repository = build_service()

    notification = service.publish(
        owner_id="teacher-001",
        notification_type=(
            NotificationType.DATA_CHANGED
        ),
        priority=NotificationPriority.HIGH,
        title="Data changed",
        message="A source has changed.",
        source_module="educational_planning_v2",
        source_id="source-001",
        action_ref="teacher-data",
    )

    assert (
        notification.notification_id
        == "notification-001"
    )

    assert (
        notification.status
        is NotificationStatus.UNREAD
    )

    assert notification.created_at == _FIXED_TIME

    assert (
        repository.rows[
            "notification-001"
        ]
        == notification
    )


def test_publish_preserves_source_reference():
    service, _ = build_service()

    notification = service.publish(
        owner_id="teacher-001",
        notification_type=(
            NotificationType.ASSIGNMENT_CHANGED
        ),
        title="Assignment changed",
        message="Teaching assignment changed.",
        source_module="educational_planning_v2",
        source_id="assignment-001",
        action_ref="teaching-assignment",
    )

    assert (
        notification.source_id
        == "assignment-001"
    )

    assert (
        notification.action_ref
        == "teaching-assignment"
    )


def test_count_unread_is_owner_scoped():
    repository = FakeNotificationRepository()

    service = NotificationService(
        repository=repository,
        id_factory=iter(
            ("n-1", "n-2")
        ).__next__,
        clock=lambda: _FIXED_TIME,
    )

    service.publish(
        owner_id="teacher-001",
        notification_type=NotificationType.SYSTEM,
        title="One",
        message="Message",
        source_module="portal_v2",
    )

    service.publish(
        owner_id="teacher-002",
        notification_type=NotificationType.SYSTEM,
        title="Two",
        message="Message",
        source_module="portal_v2",
    )

    assert (
        service.count_unread(
            owner_id="teacher-001"
        )
        == 1
    )


def test_mark_read_uses_service_clock():
    service, _ = build_service()

    service.publish(
        owner_id="teacher-001",
        notification_type=NotificationType.SYSTEM,
        title="Notice",
        message="Message",
        source_module="portal_v2",
    )

    updated = service.mark_read(
        notification_id="notification-001",
        owner_id="teacher-001",
    )

    assert updated is not None

    assert (
        updated.status
        is NotificationStatus.READ
    )

    assert updated.read_at == _FIXED_TIME


def test_mark_read_cannot_cross_owner_boundary():
    service, _ = build_service()

    service.publish(
        owner_id="teacher-001",
        notification_type=NotificationType.SYSTEM,
        title="Notice",
        message="Message",
        source_module="portal_v2",
    )

    updated = service.mark_read(
        notification_id="notification-001",
        owner_id="teacher-999",
    )

    assert updated is None


def test_mark_all_read_affects_only_owner():
    repository = FakeNotificationRepository()

    service = NotificationService(
        repository=repository,
        id_factory=iter(
            ("n-1", "n-2", "n-3")
        ).__next__,
        clock=lambda: _FIXED_TIME,
    )

    for owner_id in (
        "teacher-001",
        "teacher-001",
        "teacher-002",
    ):
        service.publish(
            owner_id=owner_id,
            notification_type=(
                NotificationType.SYSTEM
            ),
            title="Notice",
            message="Message",
            source_module="portal_v2",
        )

    changed = service.mark_all_read(
        owner_id="teacher-001"
    )

    assert changed == 2

    assert (
        service.count_unread(
            owner_id="teacher-001"
        )
        == 0
    )

    assert (
        service.count_unread(
            owner_id="teacher-002"
        )
        == 1
    )
