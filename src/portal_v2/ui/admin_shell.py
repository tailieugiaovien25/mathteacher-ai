from __future__ import annotations
from portal_v2.ui.admin_subject_coordination_workspace_streamlit import render_admin_subject_coordination_workspace

from typing import Any

from portal_v2.authorization import PortalAuthorizationContext
from portal_v2.ui.admin_user_registration_review_streamlit import render_admin_user_registration_review
from portal_v2.ui.admin_subject_catalog_streamlit import (
    render_admin_subject_catalog,
)
from portal_v2.ui.admin_class_catalog_streamlit import (
    render_admin_class_catalog,
)
from portal_v2.ui.admin_competency_catalog_streamlit import (
    render_admin_competency_catalog,
)
from portal_v2.ui.admin_learning_content_catalog_streamlit import (
    render_admin_learning_content_catalog,
)
from portal_v2.ui.admin_assignment_workspace_streamlit import (
    render_admin_assignment_workspace,
)
from portal_v2.ui.admin_academic_year_configuration_streamlit import (
    render_admin_academic_year_configuration,
)
from portal_v2.ui.admin_canonical_code_catalog_streamlit import (
    render_admin_canonical_code_catalog,
)
from portal_v2.ui.admin_context_control_center_streamlit import (
    render_admin_context_control_center,
)
from portal_v2.ui.admin_assessment_runtime_readiness_streamlit import (
    render_admin_assessment_runtime_readiness,
)
from portal_v2.ui.admin_assessment_template_workflow_streamlit import (
    render_admin_assessment_template_workflow,
)
from portal_v2.ui.admin_assessment_setting_review_streamlit import (
    render_admin_assessment_setting_review,
)

from portal_v2.ui.admin_lesson_plan_coordination_center_streamlit import (
    render_admin_lesson_plan_coordination_center,
)

from portal_v2.ui.admin_navigation import (
    ADMIN_PAGE_ACADEMIC_YEAR_CONFIGURATION,
    ADMIN_PAGE_CANONICAL_CODE_CATALOG,
    ADMIN_PAGE_CONTEXT_CONTROL_CENTER,
    ADMIN_PAGE_LESSON_PLAN_COORDINATION_CENTER,
    ADMIN_PAGE_ASSESSMENT_TEMPLATES,
    ADMIN_PAGE_ASSESSMENT_REVIEWS,
    ADMIN_PAGE_USER_REGISTRATIONS,
    ADMIN_PAGE_DASHBOARD,
    ADMIN_PAGE_SOURCES,
    ADMIN_PAGE_SYSTEM_HEALTH,
    ADMIN_PAGE_SUBJECT_CATALOG,
    ADMIN_PAGE_CLASS_CATALOG,
    ADMIN_PAGE_COMPETENCY_CATALOG,
    ADMIN_PAGE_LEARNING_CONTENT_CATALOG,
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
        .in_("role", ("teacher", "admin"))
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
                "role": str(role_row.get("role", "") or "").strip().lower(),
                "teacher_code": str((profile or {}).get("teacher_code", "") or ""),
                "full_name": str((profile or {}).get("full_name", "") or ""),
                "school_name": str((profile or {}).get("school_name", "") or ""),
                "registered_at": str(role_row.get("created_at", "") or ""),
                "is_active": role_row.get("is_active", True) is True,
                "status": (
                    "Má»›i Ä‘Äƒng kÃ½"
                    if profile is None
                    else (
                        "Äang cÃ³ hiá»‡u lá»±c"
                        if role_row.get("is_active", True) is True
                        else "Ngá»«ng hoáº¡t Ä‘á»™ng"
                    )
                ),
            }
        )

    return tuple(
        sorted(
            result,
            key=lambda item: (
                {
                    "Má»›i Ä‘Äƒng kÃ½": 0,
                    "Äang cÃ³ hiá»‡u lá»±c": 1,
                    "Ngá»«ng hoáº¡t Ä‘á»™ng": 2,
                }.get(item["status"], 3),
                item["full_name"].casefold(),
                item["registered_at"],
            ),
        )
    )


def _render_admin_dashboard(st, *, client=None) -> None:
    st.title("ADMIN Dashboard")
    st.caption(
        "Tá»•ng quan váº­n hÃ nh vÃ  quáº£n trá»‹ dá»¯ liá»‡u tin cáº­y cá»§a MathTeacher-AI."
    )

    if client is None:
        st.warning("ChÆ°a cÃ³ káº¿t ná»‘i dá»¯ liá»‡u Ä‘á»ƒ táº£i danh sÃ¡ch USER.")
        return

    try:
        user_rows = _load_admin_user_directory(client=client)
    except Exception as error:
        st.error(f"KhÃ´ng thá»ƒ táº£i danh sÃ¡ch USER: {error}")
        return

    new_count = sum(
        item["status"] == "Má»›i Ä‘Äƒng kÃ½"
        for item in user_rows
    )
    active_count = sum(
        item["status"] == "Äang cÃ³ hiá»‡u lá»±c"
        for item in user_rows
    )

    metric_columns = st.columns(3)
    metric_columns[0].metric("Tá»•ng USER", len(user_rows))
    metric_columns[1].metric("Má»›i Ä‘Äƒng kÃ½", new_count)
    metric_columns[2].metric("Äang cÃ³ hiá»‡u lá»±c", active_count)

    status_filter = st.segmented_control(
        "Tráº¡ng thÃ¡i USER",
        options=(
            "Táº¥t cáº£",
            "Má»›i Ä‘Äƒng kÃ½",
            "Äang cÃ³ hiá»‡u lá»±c",
            "Ngá»«ng hoáº¡t Ä‘á»™ng",
        ),
        default="Táº¥t cáº£",
        key="admin_dashboard_user_status",
    )
    visible_rows = tuple(
        item
        for item in user_rows
        if status_filter in (None, "Táº¥t cáº£")
        or item["status"] == status_filter
    )

    st.dataframe(
        [
            {
                "Tráº¡ng thÃ¡i": item["status"],
                "Há» vÃ  tÃªn": item["full_name"] or "â€” ChÆ°a khai há»“ sÆ¡ â€”",
                "MÃ£ giÃ¡o viÃªn": item["teacher_code"] or "â€”",
                "TrÆ°á»ng": item["school_name"] or "â€”",
                "NgÃ y Ä‘Äƒng kÃ½": item["registered_at"][:10] or "â€”",
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
        "Quáº£n trá»‹ dá»¯ liá»‡u theo vÃ²ng Ä‘á»i Draft â†’ Pending â†’ Verified â†’ Published."
    )
    st.info("Danh sÃ¡ch vÃ  workflow dá»¯ liá»‡u tháº­t sáº½ Ä‘Æ°á»£c ná»‘i á»Ÿ bÆ°á»›c tiáº¿p theo.")


def _render_time_allocation(st) -> None:
    st.title("Time Allocation")
    st.caption(
        "Quáº£n trá»‹ phÃ¢n bá»• thá»i lÆ°á»£ng theo curriculum, subject vÃ  grade."
    )
    st.info(
        "KhÃ´ng hard-code sá»‘ tiáº¿t trong UI. GiÃ¡ trá»‹ sáº½ Ä‘áº¿n tá»« dá»¯ liá»‡u quáº£n trá»‹."
    )


def _render_sources(st) -> None:
    st.title("Sources & Provenance")
    st.caption(
        "Quáº£n trá»‹ nguá»“n, phiÃªn báº£n nguá»“n vÃ  truy váº¿t provenance."
    )
    st.info("Nguá»“n dá»¯ liá»‡u tháº­t sáº½ Ä‘Æ°á»£c ná»‘i qua service boundary.")


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
        raise ValueError("KhÃ´ng tÃ¬m tháº¥y tÃ i khoáº£n giÃ¡o viÃªn cáº§n cáº­p nháº­t.")


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
        raise ValueError("MÃ£ giÃ¡o viÃªn, há» tÃªn vÃ  trÆ°á»ng khÃ´ng Ä‘Æ°á»£c Ä‘á»ƒ trá»‘ng.")
    (
        client.table("teacher_profiles")
        .update(values)
        .eq("user_id", user_id)
        .execute()
    )


def _render_users(st, *, client=None) -> None:
    st.title("NgÆ°á»i dÃ¹ng & Quyá»n háº¡n")
    st.caption(
        "Quáº£n lÃ½ há»“ sÆ¡, tráº¡ng thÃ¡i tÃ i khoáº£n vÃ  má»Ÿ nhanh phÃ¢n cÃ´ng chuyÃªn mÃ´n."
    )

    if client is None:
        st.warning("ChÆ°a cÃ³ káº¿t ná»‘i dá»¯ liá»‡u Ä‘á»ƒ táº£i danh sÃ¡ch ngÆ°á»i dÃ¹ng.")
        return

    try:
        user_rows = _load_admin_user_directory(client=client)
    except Exception as error:
        st.error(f"KhÃ´ng thá»ƒ táº£i danh sÃ¡ch ngÆ°á»i dÃ¹ng: {error}")
        return

    active_count = sum(item["status"] == "Äang cÃ³ hiá»‡u lá»±c" for item in user_rows)
    stopped_count = sum(item["status"] == "Ngá»«ng hoáº¡t Ä‘á»™ng" for item in user_rows)
    new_count = sum(item["status"] == "Má»›i Ä‘Äƒng kÃ½" for item in user_rows)

    metrics = st.columns(4)
    metrics[0].metric("Tá»•ng USER", len(user_rows))
    metrics[1].metric("Má»›i Ä‘Äƒng kÃ½", new_count)
    metrics[2].metric("Äang cÃ³ hiá»‡u lá»±c", active_count)
    metrics[3].metric("Ngá»«ng hoáº¡t Ä‘á»™ng", stopped_count)

    status_filter = st.segmented_control(
        "Tráº¡ng thÃ¡i USER",
        options=("Táº¥t cáº£", "Má»›i Ä‘Äƒng kÃ½", "Äang cÃ³ hiá»‡u lá»±c", "Ngá»«ng hoáº¡t Ä‘á»™ng"),
        default="Táº¥t cáº£",
        key="admin_users_status_filter",
    )
    visible_rows = tuple(
        item for item in user_rows
        if status_filter in (None, "Táº¥t cáº£") or item["status"] == status_filter
    )

    headers = st.columns([1.35, 1.8, 1.0, 2.2, 1.1, 2.6])
    for column, label in zip(
        headers,
        ("Tráº¡ng thÃ¡i", "Há» vÃ  tÃªn", "MÃ£ GV", "TrÆ°á»ng", "NgÃ y Ä‘Äƒng kÃ½", "Thao tÃ¡c"),
    ):
        column.markdown(f"**{label}**")

    if not visible_rows:
        st.info("KhÃ´ng cÃ³ ngÆ°á»i dÃ¹ng phÃ¹ há»£p vá»›i bá»™ lá»c.")

    for item in visible_rows:
        columns = st.columns([1.35, 1.8, 1.0, 2.2, 1.1, 2.6])
        columns[0].write(item["status"])
        columns[1].write(item["full_name"] or "â€” ChÆ°a khai há»“ sÆ¡ â€”")
        columns[2].write(item["teacher_code"] or "â€”")
        columns[3].write(item["school_name"] or "â€”")
        columns[4].write(item["registered_at"][:10] or "â€”")

        action_columns = columns[5].columns(3)
        if action_columns[0].button(
            "Chá»‰nh sá»­a",
            key=f"admin_user_edit_{item['user_id']}",
            disabled=not bool(item["full_name"]),
            width="stretch",
        ):
            st.session_state["admin_user_edit_id"] = item["user_id"]
            st.rerun()

        if action_columns[1].button(
            "PhÃ¢n cÃ´ng",
            key=f"admin_user_assign_{item['user_id']}",
            disabled=item["status"] != "Äang cÃ³ hiá»‡u lá»±c",
            width="stretch",
        ):
            st.session_state["admin_assignment_target_teacher_id"] = item["user_id"]
            st.session_state["admin_portal_navigation_target"] = ADMIN_PAGE_ASSIGNMENTS
            st.rerun()

        is_protected_admin = item["role"] == "admin"
        toggle_label = (
            "Báº£o vá»‡"
            if is_protected_admin
            else ("Ngá»«ng" if item["is_active"] else "KÃ­ch hoáº¡t")
        )
        if action_columns[2].button(
            toggle_label,
            key=f"admin_user_toggle_{item['user_id']}",
            disabled=is_protected_admin or not bool(item["full_name"]),
            width="stretch",
        ):
            try:
                _update_user_active_status(
                    client=client,
                    user_id=item["user_id"],
                    active=not item["is_active"],
                )
            except Exception as error:
                st.error(f"KhÃ´ng thá»ƒ cáº­p nháº­t tráº¡ng thÃ¡i tÃ i khoáº£n: {error}")
            else:
                st.success("ÄÃ£ cáº­p nháº­t tráº¡ng thÃ¡i tÃ i khoáº£n.")
                st.rerun()

    edit_id = st.session_state.get("admin_user_edit_id")
    edit_item = next((item for item in user_rows if item["user_id"] == edit_id), None)
    if edit_item is not None:
        st.divider()
        st.subheader("Chá»‰nh sá»­a há»“ sÆ¡ giÃ¡o viÃªn")
        with st.form("admin_user_edit_form"):
            full_name = st.text_input("Há» vÃ  tÃªn", value=edit_item["full_name"])
            teacher_code = st.text_input("MÃ£ giÃ¡o viÃªn", value=edit_item["teacher_code"])
            school_name = st.text_input("TrÆ°á»ng", value=edit_item["school_name"])
            form_columns = st.columns(2)
            save_edit = form_columns[0].form_submit_button(
                "LÆ°u thay Ä‘á»•i", type="primary", width="stretch"
            )
            cancel_edit = form_columns[1].form_submit_button(
                "Há»§y", width="stretch"
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
                st.error(f"KhÃ´ng thá»ƒ cáº­p nháº­t há»“ sÆ¡: {error}")
            else:
                st.session_state.pop("admin_user_edit_id", None)
                st.success("ÄÃ£ cáº­p nháº­t há»“ sÆ¡ giÃ¡o viÃªn.")
                st.rerun()


def render_admin_page(
    st,
    *,
    page_id: str,
    authorization,
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
        == ADMIN_PAGE_COMPETENCY_CATALOG
    ):
        render_admin_competency_catalog(
            st,
            client=client,
        )
        return

    if (
        page.page_id
        == ADMIN_PAGE_LEARNING_CONTENT_CATALOG
    ):
        render_admin_learning_content_catalog(
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

    if page.page_id == ADMIN_PAGE_CANONICAL_CODE_CATALOG:
        render_admin_canonical_code_catalog(st, client=client)
        return

    if page.page_id == ADMIN_PAGE_LESSON_PLAN_COORDINATION_CENTER:
        render_admin_lesson_plan_coordination_center(
            st,
            client=client,
        )
        return

    if page.page_id == ADMIN_PAGE_CONTEXT_CONTROL_CENTER:
        render_admin_context_control_center(
            st,
            authorization=authorization,
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
            reviewer_user_id=authorization.user_id,
        )
        return
    if page.page_id == ADMIN_PAGE_USER_REGISTRATIONS:
        render_admin_user_registration_review(client=client)
        return
    if page.page_id == ADMIN_PAGE_ASSESSMENT_REVIEWS:
        render_admin_assessment_setting_review(
            st,
            client=client,
            reviewer_user_id=authorization.user_id,
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
        "Quáº£n trá»‹",
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
        authorization=authorization,
        client=client,
    )


# G1B_P1A_ADMIN_NAVIGATION
def render_admin_subject_coordination_read_only(*, client):
    return render_admin_subject_coordination_workspace(client=client)

