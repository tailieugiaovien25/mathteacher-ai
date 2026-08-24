from datetime import datetime, timezone

import pytest

from notification_v2.models import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from portal_v2.ui.notification_center_presenter import (
    NotificationCenterItem,
    NotificationCenterView,
    build_notification_center_view,
)


CREATED_AT = datetime(
    2026,
    8,
    17,
    10,
    0,
    tzinfo=timezone.utc,
)


def build_notification(
    *,
    notification_id: str = "notification-1",
    status: NotificationStatus = (
        NotificationStatus.UNREAD
    ),
    action_ref: str | None = "teacher-timetable",
) -> Notification:
    read_at = (
        CREATED_AT
        if status is NotificationStatus.READ
        else None
    )

    return Notification(
        notification_id=notification_id,
        owner_id="teacher-1",
        type=NotificationType.DATA_CHANGED,
        priority=NotificationPriority.HIGH,
        title="Dữ liệu đã thay đổi",
        message="Thời khóa biểu có dữ liệu mới.",
        source_module="educational_planning_v2",
        action_ref=action_ref,
        status=status,
        created_at=CREATED_AT,
        read_at=read_at,
    )


def test_empty_notification_center():
    view = build_notification_center_view(
        notifications=(),
        unread_count=0,
    )

    assert isinstance(
        view,
        NotificationCenterView,
    )
    assert view.items == ()
    assert view.unread_count == 0
    assert not view.has_notifications
    assert not view.has_unread


def test_notification_is_mapped_to_view_item():
    notification = build_notification()

    view = build_notification_center_view(
        notifications=(notification,),
        unread_count=1,
    )

    assert len(view.items) == 1

    item = view.items[0]

    assert isinstance(
        item,
        NotificationCenterItem,
    )
    assert (
        item.notification_id
        == notification.notification_id
    )
    assert item.title == notification.title
    assert item.message == notification.message
    assert item.type is NotificationType.DATA_CHANGED
    assert (
        item.priority
        is NotificationPriority.HIGH
    )
    assert (
        item.status
        is NotificationStatus.UNREAD
    )
    assert item.created_at == CREATED_AT
    assert item.action_ref == "teacher-timetable"
    assert item.is_unread


def test_read_notification_is_not_unread():
    notification = build_notification(
        status=NotificationStatus.READ,
    )

    view = build_notification_center_view(
        notifications=(notification,),
        unread_count=0,
    )

    assert not view.items[0].is_unread
    assert not view.has_unread


def test_action_ref_may_be_none():
    notification = build_notification(
        action_ref=None,
    )

    view = build_notification_center_view(
        notifications=(notification,),
        unread_count=1,
    )

    assert view.items[0].action_ref is None


def test_unread_count_is_preserved():
    view = build_notification_center_view(
        notifications=(
            build_notification(
                notification_id="n-1",
            ),
            build_notification(
                notification_id="n-2",
            ),
        ),
        unread_count=7,
    )

    assert view.unread_count == 7
    assert view.has_unread


def test_negative_unread_count_is_rejected():
    with pytest.raises(
        ValueError,
        match="unread_count must not be negative",
    ):
        build_notification_center_view(
            notifications=(),
            unread_count=-1,
        )
