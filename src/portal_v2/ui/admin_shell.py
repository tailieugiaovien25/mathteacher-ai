from __future__ import annotations

from typing import Any

from portal_v2.authorization import PortalAuthorizationContext
from portal_v2.ui.admin_subject_catalog_streamlit import (
    render_admin_subject_catalog,
)
from portal_v2.ui.admin_class_catalog_streamlit import (
    render_admin_class_catalog,
)
from portal_v2.ui.admin_assignment_workspace_streamlit import (
    render_admin_assignment_workspace,
)
from portal_v2.ui.admin_academic_year_configuration_streamlit import (
    render_admin_academic_year_configuration,
)

from portal_v2.ui.admin_navigation import (
    ADMIN_PAGE_ACADEMIC_YEAR_CONFIGURATION,
    ADMIN_PAGE_DASHBOARD,
    ADMIN_PAGE_SOURCES,
    ADMIN_PAGE_SYSTEM_HEALTH,
    ADMIN_PAGE_SUBJECT_CATALOG,
    ADMIN_PAGE_CLASS_CATALOG,
    ADMIN_PAGE_ASSIGNMENTS,
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


def _load_admin_user_directory(*, client) -> tuple[dict[str, str], ...]:
    """Join trusted portal roles with optional teacher profiles."""

    role_response = (
        client.table("portal_roles")
        .select("user_id,role,created_at")
        .eq("role", "teacher")
        .execute()
    )
    profile_response = (
        client.table("teacher_profiles")
        .select(
            "user_id,teacher_code,full_name,school_name,created_at"
        )
        .execute()
    )

    role_rows = tuple(getattr(role_response, "data", ()) or ())
    profile_rows = tuple(getattr(profile_response, "data", ()) or ())
    profiles_by_user = {
        str(item.get("user_id", "") or ""): item
        for item in profile_rows
        if isinstance(item, dict)
    }

    result = []
    for role_row in role_rows:
        if not isinstance(role_row, dict):
            continue
        user_id = str(role_row.get("user_id", "") or "").strip()
        if not user_id:
            continue
        profile = profiles_by_user.get(user_id)
        result.append(
            {
                "user_id": user_id,
                "teacher_code": str((profile or {}).get("teacher_code", "") or ""),
                "full_name": str((profile or {}).get("full_name", "") or ""),
                "school_name": str((profile or {}).get("school_name", "") or ""),
                "registered_at": str(role_row.get("created_at", "") or ""),
                "status": (
                    "Đã là người dùng"
                    if profile is not None
                    else "Mới đăng ký"
                ),
            }
        )

    return tuple(
        sorted(
            result,
            key=lambda item: (
                0 if item["status"] == "Mới đăng ký" else 1,
                item["full_name"].casefold(),
                item["registered_at"],
            ),
        )
    )


def _render_admin_dashboard(st, *, client=None) -> None:
    st.title("ADMIN Dashboard")
    st.caption(
        "Tổng quan vận hành và quản trị dữ liệu tin cậy của MathTeacher-AI."
    )

    if client is None:
        st.warning("Chưa có kết nối dữ liệu để tải danh sách USER.")
        return

    try:
        user_rows = _load_admin_user_directory(client=client)
    except Exception as error:
        st.error(f"Không thể tải danh sách USER: {error}")
        return

    new_count = sum(
        item["status"] == "Mới đăng ký"
        for item in user_rows
    )
    active_count = len(user_rows) - new_count

    metric_columns = st.columns(3)
    metric_columns[0].metric("Tổng USER", len(user_rows))
    metric_columns[1].metric("Mới đăng ký", new_count)
    metric_columns[2].metric("Đã là người dùng", active_count)

    status_filter = st.segmented_control(
        "Trạng thái USER",
        options=("Tất cả", "Mới đăng ký", "Đã là người dùng"),
        default="Tất cả",
        key="admin_dashboard_user_status",
    )
    visible_rows = tuple(
        item
        for item in user_rows
        if status_filter in (None, "Tất cả")
        or item["status"] == status_filter
    )

    st.dataframe(
        [
            {
                "Trạng thái": item["status"],
                "Họ và tên": item["full_name"] or "— Chưa khai hồ sơ —",
                "Mã giáo viên": item["teacher_code"] or "—",
                "Trường": item["school_name"] or "—",
                "Ngày đăng ký": item["registered_at"][:10] or "—",
                "USER ID": item["user_id"],
            }
            for item in visible_rows
        ],
        hide_index=True,
        use_container_width=True,
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


def render_admin_page(
    st,
    *,
    page_id: str,
    client=None,
) -> None:
    page = resolve_admin_portal_page(
        page_id=page_id
    )

    if page.page_id == ADMIN_PAGE_DASHBOARD:
        _render_admin_dashboard(
            st,
            client=client,
        )
        return

    if (
        page.page_id
        == ADMIN_PAGE_SUBJECT_CATALOG
    ):
        render_admin_subject_catalog(
            st,
            client=client,
        )
        return

    if (
        page.page_id
        == ADMIN_PAGE_CLASS_CATALOG
    ):
        render_admin_class_catalog(
            st,
            client=client,
        )
        return

    if (
        page.page_id
        == ADMIN_PAGE_ASSIGNMENTS
    ):
        render_admin_assignment_workspace(
            st,
            client=client,
        )
        return

    if (
        page.page_id
        == ADMIN_PAGE_ACADEMIC_YEAR_CONFIGURATION
    ):
        render_admin_academic_year_configuration(
            st,
            client=client,
        )
        return

    renderers = {
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
    *,
    client=None,
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
        client=client,
    )
