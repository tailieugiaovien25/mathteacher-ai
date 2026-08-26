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
from portal_v2.ui.admin_assessment_runtime_readiness_streamlit import (
    render_admin_assessment_runtime_readiness,
)
from portal_v2.ui.admin_assessment_template_workflow_streamlit import (
    render_admin_assessment_template_workflow,
)

from portal_v2.ui.admin_navigation import (
    ADMIN_PAGE_ACADEMIC_YEAR_CONFIGURATION,
    ADMIN_PAGE_ASSESSMENT_TEMPLATES,
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
        .select("user_id,role,is_active,created_at")
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
                "is_active": role_row.get("is_active", True) is True,
                "status": (
                    "Mới đăng ký"
                    if profile is None
                    else (
                        "Đang có hiệu lực"
                        if role_row.get("is_active", True) is True
                        else "Ngừng hoạt động"
                    )
                ),
            }
        )

    return tuple(
        sorted(
            result,
            key=lambda item: (
                {
                    "Mới đăng ký": 0,
                    "Đang có hiệu lực": 1,
                    "Ngừng hoạt động": 2,
                }.get(item["status"], 3),
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
    active_count = sum(
        item["status"] == "Đang có hiệu lực"
        for item in user_rows
    )

    metric_columns = st.columns(3)
    metric_columns[0].metric("Tổng USER", len(user_rows))
    metric_columns[1].metric("Mới đăng ký", new_count)
    metric_columns[2].metric("Đang có hiệu lực", active_count)

    status_filter = st.segmented_control(
        "Trạng thái USER",
        options=(
            "Tất cả",
            "Mới đăng ký",
            "Đang có hiệu lực",
            "Ngừng hoạt động",
        ),
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


def _update_user_active_status(*, client, user_id: str, active: bool) -> None:
    response = (
        client.table("portal_roles")
        .update({"is_active": active})
        .eq("user_id", user_id)
        .eq("role", "teacher")
        .execute()
    )
    rows = getattr(response, "data", None)
    if isinstance(rows, list) and not rows:
        raise ValueError("Không tìm thấy tài khoản giáo viên cần cập nhật.")


def _update_teacher_profile(
    *,
    client,
    user_id: str,
    teacher_code: str,
    full_name: str,
    school_name: str,
) -> None:
    values = {
        "teacher_code": teacher_code.strip(),
        "full_name": full_name.strip(),
        "school_name": school_name.strip(),
    }
    if not all(values.values()):
        raise ValueError("Mã giáo viên, họ tên và trường không được để trống.")
    (
        client.table("teacher_profiles")
        .update(values)
        .eq("user_id", user_id)
        .execute()
    )


def _render_users(st, *, client=None) -> None:
    st.title("Người dùng & Quyền hạn")
    st.caption(
        "Quản lý hồ sơ, trạng thái tài khoản và mở nhanh phân công chuyên môn."
    )

    if client is None:
        st.warning("Chưa có kết nối dữ liệu để tải danh sách người dùng.")
        return

    try:
        user_rows = _load_admin_user_directory(client=client)
    except Exception as error:
        st.error(f"Không thể tải danh sách người dùng: {error}")
        return

    active_count = sum(item["status"] == "Đang có hiệu lực" for item in user_rows)
    stopped_count = sum(item["status"] == "Ngừng hoạt động" for item in user_rows)
    new_count = sum(item["status"] == "Mới đăng ký" for item in user_rows)

    metrics = st.columns(4)
    metrics[0].metric("Tổng USER", len(user_rows))
    metrics[1].metric("Mới đăng ký", new_count)
    metrics[2].metric("Đang có hiệu lực", active_count)
    metrics[3].metric("Ngừng hoạt động", stopped_count)

    status_filter = st.segmented_control(
        "Trạng thái USER",
        options=("Tất cả", "Mới đăng ký", "Đang có hiệu lực", "Ngừng hoạt động"),
        default="Tất cả",
        key="admin_users_status_filter",
    )
    visible_rows = tuple(
        item for item in user_rows
        if status_filter in (None, "Tất cả") or item["status"] == status_filter
    )

    headers = st.columns([1.35, 1.8, 1.0, 2.2, 1.1, 2.6])
    for column, label in zip(
        headers,
        ("Trạng thái", "Họ và tên", "Mã GV", "Trường", "Ngày đăng ký", "Thao tác"),
    ):
        column.markdown(f"**{label}**")

    if not visible_rows:
        st.info("Không có người dùng phù hợp với bộ lọc.")

    for item in visible_rows:
        columns = st.columns([1.35, 1.8, 1.0, 2.2, 1.1, 2.6])
        columns[0].write(item["status"])
        columns[1].write(item["full_name"] or "— Chưa khai hồ sơ —")
        columns[2].write(item["teacher_code"] or "—")
        columns[3].write(item["school_name"] or "—")
        columns[4].write(item["registered_at"][:10] or "—")

        action_columns = columns[5].columns(3)
        if action_columns[0].button(
            "Chỉnh sửa",
            key=f"admin_user_edit_{item['user_id']}",
            disabled=not bool(item["full_name"]),
            width="stretch",
        ):
            st.session_state["admin_user_edit_id"] = item["user_id"]
            st.rerun()

        if action_columns[1].button(
            "Phân công",
            key=f"admin_user_assign_{item['user_id']}",
            disabled=item["status"] != "Đang có hiệu lực",
            width="stretch",
        ):
            st.session_state["admin_assignment_target_teacher_id"] = item["user_id"]
            st.session_state["admin_portal_navigation_target"] = ADMIN_PAGE_ASSIGNMENTS
            st.rerun()

        toggle_label = "Ngừng" if item["is_active"] else "Kích hoạt"
        if action_columns[2].button(
            toggle_label,
            key=f"admin_user_toggle_{item['user_id']}",
            disabled=not bool(item["full_name"]),
            width="stretch",
        ):
            try:
                _update_user_active_status(
                    client=client,
                    user_id=item["user_id"],
                    active=not item["is_active"],
                )
            except Exception as error:
                st.error(f"Không thể cập nhật trạng thái tài khoản: {error}")
            else:
                st.success("Đã cập nhật trạng thái tài khoản.")
                st.rerun()

    edit_id = st.session_state.get("admin_user_edit_id")
    edit_item = next((item for item in user_rows if item["user_id"] == edit_id), None)
    if edit_item is not None:
        st.divider()
        st.subheader("Chỉnh sửa hồ sơ giáo viên")
        with st.form("admin_user_edit_form"):
            full_name = st.text_input("Họ và tên", value=edit_item["full_name"])
            teacher_code = st.text_input("Mã giáo viên", value=edit_item["teacher_code"])
            school_name = st.text_input("Trường", value=edit_item["school_name"])
            form_columns = st.columns(2)
            save_edit = form_columns[0].form_submit_button(
                "Lưu thay đổi", type="primary", width="stretch"
            )
            cancel_edit = form_columns[1].form_submit_button(
                "Hủy", width="stretch"
            )

        if cancel_edit:
            st.session_state.pop("admin_user_edit_id", None)
            st.rerun()
        if save_edit:
            try:
                _update_teacher_profile(
                    client=client,
                    user_id=edit_item["user_id"],
                    teacher_code=teacher_code,
                    full_name=full_name,
                    school_name=school_name,
                )
            except Exception as error:
                st.error(f"Không thể cập nhật hồ sơ: {error}")
            else:
                st.session_state.pop("admin_user_edit_id", None)
                st.success("Đã cập nhật hồ sơ giáo viên.")
                st.rerun()


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
    }

    if page.page_id == ADMIN_PAGE_USERS:
        _render_users(st, client=client)
        return

    if page.page_id == ADMIN_PAGE_SYSTEM_HEALTH:
        render_admin_assessment_runtime_readiness(
            st,
            client=client,
        )
        return

    if page.page_id == ADMIN_PAGE_ASSESSMENT_TEMPLATES:
        render_admin_assessment_template_workflow(
            st,
            client=client,
        )
        return

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

    navigation_target = st.session_state.pop(
        "admin_portal_navigation_target",
        None,
    )
    if navigation_target is not None:
        current_page_id = resolve_admin_portal_page(
            page_id=navigation_target,
        ).page_id
        st.session_state[ADMIN_PORTAL_SESSION_KEY] = current_page_id
        st.session_state["admin_portal_navigation"] = admin_page_label_from_id(
            page_id=current_page_id,
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
