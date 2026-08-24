from contextlib import contextmanager
from datetime import datetime, timezone

from notification_v2.models import (
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from portal_v2.ui.notification_center_presenter import (
    NotificationCenterItem,
    NotificationCenterView,
)
from portal_v2.ui.notification_center_streamlit import (
    render_notification_center_sidebar,
)


class FakeSidebar:
    def __init__(
        self,
        owner,
    ):
        self.owner = owner

    @contextmanager
    def expander(
        self,
        label,
        expanded=False,
    ):
        self.owner.expander_labels.append(
            label
        )
        yield


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked_keys=(),
    ):
        self.sidebar = FakeSidebar(
            self
        )
        self.clicked_keys = set(
            clicked_keys
        )
        self.expander_labels = []
        self.captions = []
        self.markdowns = []
        self.writes = []
        self.button_keys = []
        self.rerun_count = 0
        self.divider_count = 0

    def caption(
        self,
        value,
    ):
        self.captions.append(
            value
        )

    def markdown(
        self,
        value,
    ):
        self.markdowns.append(
            value
        )

    def write(
        self,
        value,
    ):
        self.writes.append(
            value
        )

    def button(
        self,
        label,
        *,
        key,
        use_container_width=False,
    ):
        self.button_keys.append(
            key
        )

        return (
            key
            in self.clicked_keys
        )

    def rerun(self):
        self.rerun_count += 1

    def divider(self):
        self.divider_count += 1


CREATED_AT = datetime(
    2026,
    8,
    17,
    10,
    30,
    tzinfo=timezone.utc,
)


def build_item(
    *,
    notification_id="n-1",
    unread=True,
):
    return NotificationCenterItem(
        notification_id=notification_id,
        title=(
            "D\u1eef li\u1ec7u "
            "\u0111\u00e3 thay \u0111\u1ed5i"
        ),
        message=(
            "Th\u1eddi kh\u00f3a bi\u1ec3u "
            "\u0111\u00e3 \u0111\u01b0\u1ee3c "
            "c\u1eadp nh\u1eadt."
        ),
        type=NotificationType.DATA_CHANGED,
        priority=NotificationPriority.NORMAL,
        status=(
            NotificationStatus.UNREAD
            if unread
            else NotificationStatus.READ
        ),
        created_at=CREATED_AT,
        action_ref=None,
        is_unread=unread,
    )


def test_empty_center_renders_without_actions():
    st = FakeStreamlit()

    render_notification_center_sidebar(
        st=st,
        view=NotificationCenterView(
            unread_count=0,
            items=(),
        ),
    )

    assert (
        st.expander_labels
        == ["\U0001F514 Th\u00f4ng b\u00e1o"]
    )

    assert (
        "Ch\u01b0a c\u00f3 th\u00f4ng b\u00e1o."
        in st.captions
    )

    assert st.button_keys == []


def test_unread_badge_is_rendered():
    st = FakeStreamlit()

    render_notification_center_sidebar(
        st=st,
        view=NotificationCenterView(
            unread_count=3,
            items=(
                build_item(),
            ),
        ),
    )

    assert (
        st.expander_labels
        == [
            "\U0001F514 Th\u00f4ng b\u00e1o (3)"
        ]
    )


def test_unread_item_renders_mark_read_action():
    st = FakeStreamlit()

    render_notification_center_sidebar(
        st=st,
        view=NotificationCenterView(
            unread_count=1,
            items=(
                build_item(),
            ),
        ),
        on_mark_read=lambda notification_id: None,
    )

    assert (
        "notification_mark_read_n-1"
        in st.button_keys
    )


def test_unread_item_without_callback_has_no_action():
    st = FakeStreamlit()

    render_notification_center_sidebar(
        st=st,
        view=NotificationCenterView(
            unread_count=1,
            items=(
                build_item(),
            ),
        ),
    )

    assert (
        "notification_mark_read_n-1"
        not in st.button_keys
    )


def test_read_item_has_no_mark_read_action():
    st = FakeStreamlit()

    render_notification_center_sidebar(
        st=st,
        view=NotificationCenterView(
            unread_count=0,
            items=(
                build_item(
                    unread=False
                ),
            ),
        ),
    )

    assert (
        "notification_mark_read_n-1"
        not in st.button_keys
    )


def test_mark_read_callback_is_invoked():
    called = []

    st = FakeStreamlit(
        clicked_keys=(
            "notification_mark_read_n-1",
        )
    )

    render_notification_center_sidebar(
        st=st,
        view=NotificationCenterView(
            unread_count=1,
            items=(
                build_item(),
            ),
        ),
        on_mark_read=called.append,
    )

    assert called == ["n-1"]
    assert st.rerun_count == 1


def test_mark_all_read_callback_is_invoked():
    called = []

    st = FakeStreamlit(
        clicked_keys=(
            "notification_mark_all_read",
        )
    )

    render_notification_center_sidebar(
        st=st,
        view=NotificationCenterView(
            unread_count=2,
            items=(
                build_item(
                    notification_id="n-1"
                ),
                build_item(
                    notification_id="n-2"
                ),
            ),
        ),
        on_mark_all_read=lambda: (
            called.append("all")
        ),
    )

    assert called == ["all"]
    assert st.rerun_count == 1


def test_notification_content_is_rendered():
    st = FakeStreamlit()

    render_notification_center_sidebar(
        st=st,
        view=NotificationCenterView(
            unread_count=1,
            items=(
                build_item(),
            ),
        ),
    )

    assert any(
        "D\u1eef li\u1ec7u"
        in value
        for value in st.markdowns
    )

    assert (
        "Th\u1eddi kh\u00f3a bi\u1ec3u "
        "\u0111\u00e3 \u0111\u01b0\u1ee3c "
        "c\u1eadp nh\u1eadt."
        in st.writes
    )

    assert (
        "17/08/2026 10:30"
        in st.captions
    )
