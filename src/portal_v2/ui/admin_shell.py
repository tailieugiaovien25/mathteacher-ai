from __future__ import annotations

from typing import Any

from portal_v2.authorization import PortalAuthorizationContext
from portal_v2.ui.admin_navigation import (
    ADMIN_PAGE_DASHBOARD,
    ADMIN_PAGE_SOURCES,
    ADMIN_PAGE_SYSTEM_HEALTH,
    ADMIN_PAGE_TIME_ALLOCATION,
    ADMIN_PAGE_TRUSTED_DATA,
    ADMIN_PAGE_USERS,
    admin_portal_page_labels,
    admin_portal_pages,
    resolve_admin_portal_page,
)


ADMIN_PORTAL_SESSION_KEY = "admin_portal_page"


def admin_page_id_from_label(*, label: str) -> str:
    if not isinstance(label, str):
        raise TypeError("label must be str")

    normalized = label.strip()
    if not normalized:
        raise ValueError("label must not be empty")

    for page in admin_portal_pages():
        if page.label == normalized:
            return page.page_id

    raise ValueError(f"unknown admin portal label: {normalized}")


def admin_page_label_from_id(*, page_id: str) -> str:
    return resolve_admin_portal_page(page_id=page_id).label


def select_admin_portal_page(
    session_state: Any,
    *,
    page_id: str,
) -> None:
    page = resolve_admin_portal_page(page_id=page_id)
    session_state[ADMIN_PORTAL_SESSION_KEY] = page.page_id


def _render_admin_dashboard(st) -> None:
    st.title("ADMIN Dashboard")
    st.caption(
        "Tổng quan vận hành và quản trị dữ liệu tin cậy của MathTeacher-AI."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Draft", "—")
    col2.metric("Pending", "—")
    col3.metric("Verified", "—")
    col4.metric("Published", "—")

    st.info(
        "UI Shell đã sẵn sàng. Dữ liệu thật sẽ được nối qua "
        "application/service boundary ở các hoạt động tiếp theo."
    )


def _render_trusted_data(st) -> None:
    st.title("Trusted Data")
    st.caption(
        "Quản trị dữ liệu theo vòng đời Draft → Pending → Verified → Published."
    )
    st.info("Danh sách và workflow dữ liệu thật sẽ được nối ở bước tiếp theo.")


def _render_time_allocation(st) -> None:
    st.title("Time Allocation")
    st.caption(
        "Quản trị phân bổ thời lượng theo curriculum, subject và grade."
    )
    st.info(
        "Không hard-code số tiết trong UI. Giá trị sẽ đến từ dữ liệu quản trị."
    )


def _render_sources(st) -> None:
    st.title("Sources & Provenance")
    st.caption(
        "Quản trị nguồn, phiên bản nguồn và truy vết provenance."
    )
    st.info("Nguồn dữ liệu thật sẽ được nối qua service boundary.")


def _render_users(st) -> None:
    st.title("Users & Permissions")
    st.caption(
        "Quản trị vai trò và quyền ENTER / VERIFY / PUBLISH / SUPERSEDE."
    )
    st.info(
        "UI không suy ra quyền từ email. Quyền phải đến từ authorization source."
    )


def _render_system_health(st) -> None:
    st.title("System Health")
    st.caption(
        "Theo dõi trạng thái dữ liệu, provider, persistence và architecture guards."
    )
    st.info("Health services sẽ được nối sau khi UI shell được khóa.")


def render_admin_page(st, *, page_id: str) -> None:
    page = resolve_admin_portal_page(page_id=page_id)

    renderers = {
        ADMIN_PAGE_DASHBOARD: _render_admin_dashboard,
        ADMIN_PAGE_TRUSTED_DATA: _render_trusted_data,
        ADMIN_PAGE_TIME_ALLOCATION: _render_time_allocation,
        ADMIN_PAGE_SOURCES: _render_sources,
        ADMIN_PAGE_USERS: _render_users,
        ADMIN_PAGE_SYSTEM_HEALTH: _render_system_health,
    }

    renderers[page.page_id](st)


def render_admin_shell(
    st,
    authorization: PortalAuthorizationContext,
) -> None:
    if not isinstance(authorization, PortalAuthorizationContext):
        raise TypeError(
            "authorization must be PortalAuthorizationContext"
        )

    if not authorization.can_access_admin_portal:
        raise PermissionError(
            "current portal user cannot access ADMIN"
        )

    st.sidebar.markdown("---")
    st.sidebar.subheader("ADMIN")

    current_page_id = st.session_state.get(
        ADMIN_PORTAL_SESSION_KEY,
        ADMIN_PAGE_DASHBOARD,
    )

    try:
        current_label = admin_page_label_from_id(
            page_id=current_page_id,
        )
    except (TypeError, ValueError):
        current_page_id = ADMIN_PAGE_DASHBOARD
        current_label = admin_page_label_from_id(
            page_id=current_page_id,
        )

    labels = admin_portal_page_labels()

    selected_label = st.sidebar.radio(
        "Quản trị",
        labels,
        index=labels.index(current_label),
        key="admin_portal_navigation",
        label_visibility="collapsed",
    )

    selected_page_id = admin_page_id_from_label(
        label=selected_label,
    )

    st.session_state[
        ADMIN_PORTAL_SESSION_KEY
    ] = selected_page_id

    render_admin_page(
        st,
        page_id=selected_page_id,
    )
