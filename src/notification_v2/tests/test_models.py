from datetime import datetime, timezone

import pytest

from notification_v2.models import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


def build_notification():
    return Notification(
        notification_id="notification-001",
        owner_id="teacher-001",
        type=NotificationType.DATA_CHANGED,
        priority=NotificationPriority.NORMAL,
        title="Data changed",
        message="A data source has changed.",
        source_module="educational_planning_v2",
        source_id="source-001",
        action_ref="teacher-data",
    )


def test_notification_defaults_to_unread():
    notification = build_notification()

    assert (
        notification.status
        is NotificationStatus.UNREAD
    )

    assert notification.read_at is None


def test_notification_normalizes_text():
    notification = Notification(
        notification_id=" n-1 ",
        owner_id=" teacher-1 ",
        type=NotificationType.SYSTEM,
        title=" System notice ",
        message=" Message ",
        source_module=" portal_v2 ",
    )

    assert notification.notification_id == "n-1"
    assert notification.owner_id == "teacher-1"
    assert notification.title == "System notice"
    assert notification.message == "Message"
    assert notification.source_module == "portal_v2"


def test_optional_text_blank_becomes_none():
    notification = Notification(
        notification_id="n-1",
        owner_id="teacher-1",
        type=NotificationType.SYSTEM,
        title="Notice",
        message="Message",
        source_module="portal_v2",
        source_id="   ",
        action_ref="   ",
    )

    assert notification.source_id is None
    assert notification.action_ref is None


def test_mark_read_returns_new_notification():
    original = build_notification()

    read_at = datetime(
        2026,
        8,
        17,
        9,
        30,
        tzinfo=timezone.utc,
    )

    updated = original.mark_read(
        read_at=read_at
    )

    assert (
        original.status
        is NotificationStatus.UNREAD
    )

    assert (
        updated.status
        is NotificationStatus.READ
    )

    assert updated.read_at == read_at
    assert updated.notification_id == original.notification_id


def test_archive_preserves_read_timestamp():
    read_at = datetime(
        2026,
        8,
        17,
        9,
        30,
        tzinfo=timezone.utc,
    )

    notification = (
        build_notification()
        .mark_read(
            read_at=read_at
        )
        .archive()
    )

    assert (
        notification.status
        is NotificationStatus.ARCHIVED
    )

    assert notification.read_at == read_at


def test_read_requires_read_at():
    with pytest.raises(ValueError):
        Notification(
            notification_id="n-1",
            owner_id="teacher-1",
            type=NotificationType.SYSTEM,
            title="Notice",
            message="Message",
            source_module="portal_v2",
            status=NotificationStatus.READ,
        )


def test_unread_must_not_have_read_at():
    with pytest.raises(ValueError):
        Notification(
            notification_id="n-1",
            owner_id="teacher-1",
            type=NotificationType.SYSTEM,
            title="Notice",
            message="Message",
            source_module="portal_v2",
            status=NotificationStatus.UNREAD,
            read_at=datetime.now(
                timezone.utc
            ),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "notification_id",
        "owner_id",
        "title",
        "message",
        "source_module",
    ),
)
def test_required_text_cannot_be_blank(
    field_name,
):
    values = {
        "notification_id": "n-1",
        "owner_id": "teacher-1",
        "type": NotificationType.SYSTEM,
        "title": "Notice",
        "message": "Message",
        "source_module": "portal_v2",
    }

    values[field_name] = "   "

    with pytest.raises(ValueError):
        Notification(**values)


def test_notification_type_is_required_enum():
    with pytest.raises(
        TypeError,
        match="type must be NotificationType",
    ):
        Notification(
            notification_id="n-1",
            owner_id="teacher-1",
            type="SYSTEM",
            title="Notice",
            message="Message",
            source_module="portal_v2",
        )


def test_priority_is_required_enum():
    with pytest.raises(TypeError):
        Notification(
            notification_id="n-1",
            owner_id="teacher-1",
            type=NotificationType.SYSTEM,
            priority="HIGH",
            title="Notice",
            message="Message",
            source_module="portal_v2",
        )


def test_created_at_requires_datetime():
    with pytest.raises(TypeError):
        Notification(
            notification_id="n-1",
            owner_id="teacher-1",
            type=NotificationType.SYSTEM,
            title="Notice",
            message="Message",
            source_module="portal_v2",
            created_at="2026-08-17",
        )


def test_created_at_uses_per_instance_factory():
    first = Notification(
        notification_id="n-1",
        owner_id="teacher-1",
        type=NotificationType.SYSTEM,
        title="First",
        message="Message",
        source_module="portal_v2",
    )

    second = Notification(
        notification_id="n-2",
        owner_id="teacher-1",
        type=NotificationType.SYSTEM,
        title="Second",
        message="Message",
        source_module="portal_v2",
    )

    assert first.created_at is not second.created_at
