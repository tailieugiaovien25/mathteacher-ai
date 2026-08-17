import pytest

from portal_v2.ui.portal_flash_feedback import (
    PORTAL_FLASH_SESSION_KEY,
    PortalFlashLevel,
    PortalFlashMessage,
    pop_portal_flash,
    render_portal_flash,
    set_portal_flash,
)


class FakeStreamlit:
    def __init__(self):
        self.success_messages = []
        self.info_messages = []
        self.warning_messages = []
        self.error_messages = []

    def success(
        self,
        message,
    ):
        self.success_messages.append(
            message
        )

    def info(
        self,
        message,
    ):
        self.info_messages.append(
            message
        )

    def warning(
        self,
        message,
    ):
        self.warning_messages.append(
            message
        )

    def error(
        self,
        message,
    ):
        self.error_messages.append(
            message
        )


def test_flash_message_normalizes_text():
    flash = PortalFlashMessage(
        message="  Saved successfully  "
    )

    assert (
        flash.message
        == "Saved successfully"
    )


def test_blank_flash_message_is_rejected():
    with pytest.raises(
        ValueError,
        match="message must not be empty",
    ):
        PortalFlashMessage(
            message="   "
        )


def test_flash_level_must_be_enum():
    with pytest.raises(
        TypeError,
        match="level must be PortalFlashLevel",
    ):
        PortalFlashMessage(
            message="Saved",
            level="SUCCESS",
        )


def test_set_flash_persists_in_session():
    state = {}

    flash = set_portal_flash(
        state,
        message="Saved",
    )

    assert (
        state[
            PORTAL_FLASH_SESSION_KEY
        ]
        is flash
    )


def test_pop_flash_consumes_once():
    state = {}

    set_portal_flash(
        state,
        message="Saved",
    )

    first = pop_portal_flash(
        state
    )

    second = pop_portal_flash(
        state
    )

    assert first is not None
    assert first.message == "Saved"
    assert second is None


@pytest.mark.parametrize(
    (
        "level",
        "attribute_name",
    ),
    (
        (
            PortalFlashLevel.SUCCESS,
            "success_messages",
        ),
        (
            PortalFlashLevel.INFO,
            "info_messages",
        ),
        (
            PortalFlashLevel.WARNING,
            "warning_messages",
        ),
        (
            PortalFlashLevel.ERROR,
            "error_messages",
        ),
    ),
)
def test_render_flash_routes_level(
    level,
    attribute_name,
):
    st = FakeStreamlit()
    state = {}

    set_portal_flash(
        state,
        message="Operation completed",
        level=level,
    )

    rendered = render_portal_flash(
        st=st,
        session_state=state,
    )

    assert rendered is not None

    assert (
        getattr(
            st,
            attribute_name,
        )
        == ["Operation completed"]
    )

    assert (
        PORTAL_FLASH_SESSION_KEY
        not in state
    )


def test_render_without_flash_is_noop():
    st = FakeStreamlit()

    assert (
        render_portal_flash(
            st=st,
            session_state={},
        )
        is None
    )

    assert st.success_messages == []
    assert st.info_messages == []
    assert st.warning_messages == []
    assert st.error_messages == []



def test_render_flash_prefers_toast_when_available():
    class ToastStreamlit(FakeStreamlit):
        def __init__(self):
            super().__init__()
            self.toasts = []

        def toast(
            self,
            message,
            *,
            icon=None,
        ):
            self.toasts.append(
                (message, icon)
            )

    st = ToastStreamlit()
    state = {}

    set_portal_flash(
        state,
        message="Saved successfully",
        level=PortalFlashLevel.SUCCESS,
    )

    rendered = render_portal_flash(
        st=st,
        session_state=state,
    )

    assert rendered is not None

    assert st.toasts == [
        (
            "Saved successfully",
            "\u2705",
        )
    ]

    assert st.success_messages == []

    assert (
        PORTAL_FLASH_SESSION_KEY
        not in state
    )
