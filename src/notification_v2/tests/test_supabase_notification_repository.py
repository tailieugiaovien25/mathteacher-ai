from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from notification_v2.adapters.supabase_notification_repository import (
    SupabaseNotificationRepository,
)
from notification_v2.models import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


@dataclass
class Response:
    data: list


class FakeQuery:
    def __init__(
        self,
        client,
    ):
        self.client = client
        self.operation = None
        self.row = None
        self.update_values = None
        self.filters = []
        self.orders = []
        self.limit_value = None

    def upsert(
        self,
        row,
        on_conflict,
    ):
        assert (
            on_conflict
            == "notification_id"
        )

        self.operation = "upsert"
        self.row = dict(row)

        return self

    def select(
        self,
        columns,
    ):
        self.operation = "select"

        return self

    def update(
        self,
        values,
    ):
        self.operation = "update"
        self.update_values = dict(
            values
        )

        return self

    def eq(
        self,
        column,
        value,
    ):
        self.filters.append(
            (column, value)
        )

        return self

    def order(
        self,
        column,
        desc=False,
    ):
        self.orders.append(
            (column, desc)
        )

        return self

    def limit(
        self,
        value,
    ):
        self.limit_value = value

        return self

    def execute(self):
        if self.operation == "upsert":
            self.client.rows[
                self.row["notification_id"]
            ] = dict(
                self.row
            )

            return Response(
                [
                    dict(
                        self.row
                    )
                ]
            )

        result = list(
            self.client.rows.values()
        )

        for column, value in self.filters:
            result = [
                row
                for row in result
                if row.get(column)
                == value
            ]

        for column, desc in reversed(
            self.orders
        ):
            result.sort(
                key=lambda row: (
                    row.get(column)
                    or ""
                ),
                reverse=desc,
            )

        if self.limit_value is not None:
            result = result[
                :self.limit_value
            ]

        if self.operation == "update":
            updated = []

            for row in result:
                notification_id = (
                    row["notification_id"]
                )

                self.client.rows[
                    notification_id
                ].update(
                    self.update_values
                )

                updated.append(
                    dict(
                        self.client.rows[
                            notification_id
                        ]
                    )
                )

            return Response(
                updated
            )

        return Response(
            [
                dict(row)
                for row in result
            ]
        )


class FakeClient:
    def __init__(self):
        self.rows = {}

    def table(
        self,
        name,
    ):
        assert (
            name
            == "notifications"
        )

        return FakeQuery(
            self
        )


def _notification(
    *,
    notification_id="notification-001",
    owner_id="user-1",
    title="Data changed",
    status=NotificationStatus.UNREAD,
    created_at=None,
):
    values = {
        "notification_id":
            notification_id,
        "owner_id":
            owner_id,
        "type":
            NotificationType.DATA_CHANGED,
        "priority":
            NotificationPriority.NORMAL,
        "title":
            title,
        "message":
            "A data source has changed.",
        "source_module":
            "educational_planning_v2",
        "source_id":
            "source-001",
        "action_ref":
            "teacher-data",
        "status":
            status,
    }

    if created_at is not None:
        values["created_at"] = (
            created_at
        )

    return Notification(
        **values
    )


def _repository():
    return (
        SupabaseNotificationRepository(
            FakeClient(),
            "user-1",
        )
    )


def test_save_and_get_notification():
    repository = _repository()

    saved = repository.save(
        notification=_notification()
    )

    assert (
        saved.notification_id
        == "notification-001"
    )

    loaded = repository.get(
        notification_id=(
            "notification-001"
        ),
        owner_id="user-1",
    )

    assert loaded is not None
    assert (
        loaded.title
        == "Data changed"
    )


def test_list_for_owner_filters_status():
    repository = _repository()

    repository.save(
        notification=_notification(
            notification_id="n-1",
        )
    )

    read_at = datetime(
        2026,
        8,
        17,
        10,
        0,
        tzinfo=timezone.utc,
    )

    repository.save(
        notification=(
            _notification(
                notification_id="n-2",
            ).mark_read(
                read_at=read_at
            )
        )
    )

    unread = repository.list_for_owner(
        owner_id="user-1",
        status=NotificationStatus.UNREAD,
    )

    assert len(unread) == 1
    assert (
        unread[0].notification_id
        == "n-1"
    )


def test_list_for_owner_orders_newest_first():
    repository = _repository()

    repository.save(
        notification=_notification(
            notification_id="old",
            created_at=datetime(
                2026,
                8,
                17,
                8,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    repository.save(
        notification=_notification(
            notification_id="new",
            created_at=datetime(
                2026,
                8,
                17,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    items = repository.list_for_owner(
        owner_id="user-1",
    )

    assert [
        item.notification_id
        for item in items
    ] == [
        "new",
        "old",
    ]


def test_list_for_owner_supports_limit():
    repository = _repository()

    for index in range(3):
        repository.save(
            notification=_notification(
                notification_id=(
                    f"n-{index}"
                ),
                created_at=datetime(
                    2026,
                    8,
                    17,
                    8 + index,
                    0,
                    tzinfo=timezone.utc,
                ),
            )
        )

    items = repository.list_for_owner(
        owner_id="user-1",
        limit=2,
    )

    assert len(items) == 2


def test_count_unread():
    repository = _repository()

    repository.save(
        notification=_notification(
            notification_id="n-1",
        )
    )

    repository.save(
        notification=_notification(
            notification_id="n-2",
        )
    )

    assert (
        repository.count_unread(
            owner_id="user-1",
        )
        == 2
    )


def test_mark_read():
    repository = _repository()

    repository.save(
        notification=_notification()
    )

    read_at = datetime(
        2026,
        8,
        17,
        10,
        30,
        tzinfo=timezone.utc,
    )

    updated = repository.mark_read(
        notification_id=(
            "notification-001"
        ),
        owner_id="user-1",
        read_at=read_at,
    )

    assert updated is not None
    assert (
        updated.status
        is NotificationStatus.READ
    )
    assert (
        updated.read_at
        == read_at
    )


def test_mark_read_missing_returns_none():
    repository = _repository()

    result = repository.mark_read(
        notification_id="missing",
        owner_id="user-1",
    )

    assert result is None


def test_mark_all_read_only_updates_unread():
    repository = _repository()

    repository.save(
        notification=_notification(
            notification_id="n-1",
        )
    )

    repository.save(
        notification=_notification(
            notification_id="n-2",
        )
    )

    count = repository.mark_all_read(
        owner_id="user-1",
        read_at=datetime(
            2026,
            8,
            17,
            11,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert count == 2

    assert (
        repository.count_unread(
            owner_id="user-1",
        )
        == 0
    )


def test_cross_owner_operations_are_blocked():
    repository = _repository()

    with pytest.raises(
        ValueError,
        match="owner_id",
    ):
        repository.list_for_owner(
            owner_id="user-2",
        )

    with pytest.raises(
        ValueError,
        match="owner_id",
    ):
        repository.count_unread(
            owner_id="user-2",
        )

    with pytest.raises(
        ValueError,
        match="owner_id",
    ):
        repository.mark_read(
            notification_id="n-1",
            owner_id="user-2",
        )


def test_cross_owner_save_is_blocked():
    repository = _repository()

    with pytest.raises(
        ValueError,
        match="owner_id",
    ):
        repository.save(
            notification=_notification(
                owner_id="user-2",
            )
        )


def test_invalid_status_filter_is_blocked():
    repository = _repository()

    with pytest.raises(TypeError):
        repository.list_for_owner(
            owner_id="user-1",
            status="UNREAD",
        )


def test_invalid_limit_is_blocked():
    repository = _repository()

    with pytest.raises(ValueError):
        repository.list_for_owner(
            owner_id="user-1",
            limit=0,
        )

    with pytest.raises(TypeError):
        repository.list_for_owner(
            owner_id="user-1",
            limit="10",
        )


def test_repository_requires_client():
    with pytest.raises(ValueError):
        SupabaseNotificationRepository(
            None,
            "user-1",
        )


def test_save_requires_notification():
    repository = _repository()

    with pytest.raises(TypeError):
        repository.save(
            notification="notification"
        )
