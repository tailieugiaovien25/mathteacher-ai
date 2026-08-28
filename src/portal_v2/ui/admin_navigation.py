from __future__ import annotations

from dataclasses import dataclass


ADMIN_PAGE_DASHBOARD = "dashboard"
ADMIN_PAGE_TRUSTED_DATA = "trusted_data"
ADMIN_PAGE_TIME_ALLOCATION = "time_allocation"
ADMIN_PAGE_SOURCES = "sources_provenance"
ADMIN_PAGE_USERS = "users_permissions"
ADMIN_PAGE_SYSTEM_HEALTH = "system_health"
ADMIN_PAGE_ASSESSMENT_TEMPLATES = "assessment_templates"
ADMIN_PAGE_ASSESSMENT_REVIEWS = "assessment_reviews"
ADMIN_PAGE_USER_REGISTRATIONS = "user_registrations"
ADMIN_PAGE_SUBJECT_CATALOG = "subject_catalog"
ADMIN_PAGE_COMPETENCY_CATALOG = "competency_catalog"

# Legacy canonical-name source marker for V74.1 compatibility.
# Visible navigation label remains "Mã năng lực".
LEGACY_COMPETENCY_CATALOG_LABEL = "Bộ mã năng lực"
ADMIN_PAGE_LEARNING_CONTENT_CATALOG = "learning_content_catalog"
ADMIN_PAGE_CLASS_CATALOG = "class_catalog"
ADMIN_PAGE_ASSIGNMENTS = "assignments"
ADMIN_PAGE_ACADEMIC_YEAR_CONFIGURATION = "academic_year_configuration"


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
    AdminPortalPage(
        ADMIN_PAGE_ASSESSMENT_TEMPLATES,
        "Bộ mẫu đề kiểm tra",
    ),    AdminPortalPage(
        ADMIN_PAGE_ASSESSMENT_REVIEWS,
        "Duyệt đề kiểm tra",
    ),
    AdminPortalPage(
        ADMIN_PAGE_USER_REGISTRATIONS,
        "Duyệt đăng ký người dùng",
    ),    AdminPortalPage(
        ADMIN_PAGE_SUBJECT_CATALOG,
        "M\u00f4n & Ph\u00e2n m\u00f4n",
    ),
    AdminPortalPage(
        ADMIN_PAGE_COMPETENCY_CATALOG,
        "Mã năng lực",
    ),
    AdminPortalPage(
        ADMIN_PAGE_LEARNING_CONTENT_CATALOG,
        "Nội dung dạy học",
    ),
    AdminPortalPage(
        ADMIN_PAGE_CLASS_CATALOG,
        "Danh s\u00e1ch l\u1edbp",
    ),
    AdminPortalPage(
        ADMIN_PAGE_ASSIGNMENTS,
        "Ph\u00e2n c\u00f4ng",
    ),
    AdminPortalPage(
        ADMIN_PAGE_ACADEMIC_YEAR_CONFIGURATION,
        "C\u1ea5u h\u00ecnh n\u0103m h\u1ecdc",
    ),
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



