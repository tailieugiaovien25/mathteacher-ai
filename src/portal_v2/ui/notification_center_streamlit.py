from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from portal_v2.ui.notification_center_presenter import (
    NotificationCenterItem,
    NotificationCenterView,
)


def render_notification_center_sidebar(
    *,
    st,
    view: NotificationCenterView,
    on_mark_read: Callable[[str], None] | None = None,
    on_mark_all_read: Callable[[], None] | None = None,
) -> None:
    label = (
        f"\U0001F514 Th\u00f4ng b\u00e1o ({view.unread_count})"
        if view.unread_count > 0
        else "\U0001F514 Th\u00f4ng b\u00e1o"
    )

    with st.sidebar.expander(
        label,
        expanded=False,
    ):
        if not view.has_notifications:
            st.caption(
                "Ch\u01b0a c\u00f3 th\u00f4ng b\u00e1o."
            )
            return

        if (
            view.has_unread
            and on_mark_all_read is not None
        ):
            if st.button(
                "\u0110\u00e1nh d\u1ea5u t\u1ea5t c\u1ea3 "
                "\u0111\u00e3 \u0111\u1ecdc",
                key="notification_mark_all_read",
                use_container_width=True,
            ):
                on_mark_all_read()
                st.rerun()

        for item in view.items:
            _render_notification_item(
                st=st,
                item=item,
                on_mark_read=on_mark_read,
            )


def _render_notification_item(
    *,
    st,
    item: NotificationCenterItem,
    on_mark_read: Callable[[str], None] | None,
) -> None:
    unread_prefix = (
        "\u25cf "
        if item.is_unread
        else ""
    )

    st.markdown(
        f"**{unread_prefix}{item.title}**"
    )

    st.write(
        item.message
    )

    st.caption(
        _format_created_at(
            item.created_at
        )
    )

    if (
        item.is_unread
        and on_mark_read is not None
    ):
        if st.button(
            "\u0110\u00e1nh d\u1ea5u \u0111\u00e3 \u0111\u1ecdc",
            key=(
                "notification_mark_read_"
                + item.notification_id
            ),
            use_container_width=True,
        ):
            on_mark_read(
                item.notification_id
            )
            st.rerun()

    st.divider()


def _format_created_at(
    value: datetime,
) -> str:
    return value.strftime(
        "%d/%m/%Y %H:%M"
    )
