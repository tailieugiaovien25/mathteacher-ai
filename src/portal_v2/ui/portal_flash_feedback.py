from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


PORTAL_FLASH_SESSION_KEY = (
    "portal_flash_feedback"
)


class PortalFlashLevel(str, Enum):
    SUCCESS = "SUCCESS"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class PortalFlashMessage:
    message: str
    level: PortalFlashLevel = (
        PortalFlashLevel.SUCCESS
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.message,
            str,
        ):
            raise TypeError(
                "message must be str"
            )

        normalized = self.message.strip()

        if not normalized:
            raise ValueError(
                "message must not be empty"
            )

        object.__setattr__(
            self,
            "message",
            normalized,
        )

        if not isinstance(
            self.level,
            PortalFlashLevel,
        ):
            raise TypeError(
                "level must be PortalFlashLevel"
            )


def set_portal_flash(
    session_state: Any,
    *,
    message: str,
    level: PortalFlashLevel = (
        PortalFlashLevel.SUCCESS
    ),
) -> PortalFlashMessage:
    flash = PortalFlashMessage(
        message=message,
        level=level,
    )

    session_state[
        PORTAL_FLASH_SESSION_KEY
    ] = flash

    return flash


def pop_portal_flash(
    session_state: Any,
) -> PortalFlashMessage | None:
    value = session_state.pop(
        PORTAL_FLASH_SESSION_KEY,
        None,
    )

    if value is None:
        return None

    if not isinstance(
        value,
        PortalFlashMessage,
    ):
        return None

    return value


def render_portal_flash(
    *,
    st,
    session_state: Any,
) -> PortalFlashMessage | None:
    flash = pop_portal_flash(
        session_state
    )

    if flash is None:
        return None

    toast = getattr(
        st,
        "toast",
        None,
    )

    if callable(toast):
        icon = {
            PortalFlashLevel.SUCCESS: "\u2705",
            PortalFlashLevel.INFO: "\u2139\ufe0f",
            PortalFlashLevel.WARNING: "\u26a0\ufe0f",
            PortalFlashLevel.ERROR: "\u274c",
        }[flash.level]

        toast(
            flash.message,
            icon=icon,
        )

        return flash

    if flash.level is PortalFlashLevel.SUCCESS:
        st.success(
            flash.message
        )

    elif flash.level is PortalFlashLevel.INFO:
        st.info(
            flash.message
        )

    elif flash.level is PortalFlashLevel.WARNING:
        st.warning(
            flash.message
        )

    else:
        st.error(
            flash.message
        )

    return flash
