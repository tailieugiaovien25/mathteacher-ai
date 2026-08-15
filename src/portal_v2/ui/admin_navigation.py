from __future__ import annotations

from dataclasses import dataclass


ADMIN_PAGE_DASHBOARD = "dashboard"
ADMIN_PAGE_TRUSTED_DATA = "trusted_data"
ADMIN_PAGE_TIME_ALLOCATION = "time_allocation"
ADMIN_PAGE_SOURCES = "sources_provenance"
ADMIN_PAGE_USERS = "users_permissions"
ADMIN_PAGE_SYSTEM_HEALTH = "system_health"


@dataclass(frozen=True)
class AdminPortalPage:
    page_id: str
    label: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "page_id",
            self._normalize_required_text(self.page_id, "page_id"),
        )
        object.__setattr__(
            self,
            "label",
            self._normalize_required_text(self.label, "label"),
        )

    @staticmethod
    def _normalize_required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be str")

        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be empty")

        return normalized


ADMIN_PORTAL_PAGES = (
    AdminPortalPage(ADMIN_PAGE_DASHBOARD, "Dashboard"),
    AdminPortalPage(ADMIN_PAGE_TRUSTED_DATA, "Trusted Data"),
    AdminPortalPage(ADMIN_PAGE_TIME_ALLOCATION, "Time Allocation"),
    AdminPortalPage(ADMIN_PAGE_SOURCES, "Sources & Provenance"),
    AdminPortalPage(ADMIN_PAGE_USERS, "Users & Permissions"),
    AdminPortalPage(ADMIN_PAGE_SYSTEM_HEALTH, "System Health"),
)


def admin_portal_pages() -> tuple[AdminPortalPage, ...]:
    return ADMIN_PORTAL_PAGES


def admin_portal_page_ids() -> tuple[str, ...]:
    return tuple(page.page_id for page in ADMIN_PORTAL_PAGES)


def admin_portal_page_labels() -> tuple[str, ...]:
    return tuple(page.label for page in ADMIN_PORTAL_PAGES)


def resolve_admin_portal_page(*, page_id: str) -> AdminPortalPage:
    if not isinstance(page_id, str):
        raise TypeError("page_id must be str")

    normalized = page_id.strip()
    if not normalized:
        raise ValueError("page_id must not be empty")

    for page in ADMIN_PORTAL_PAGES:
        if page.page_id == normalized:
            return page

    raise ValueError(f"unknown admin portal page: {normalized}")
