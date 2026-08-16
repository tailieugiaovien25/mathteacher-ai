"""Unified Streamlit portal for MathTeacher-AI teacher tools."""

from __future__ import annotations

import os
from typing import Any, Mapping

from educational_planning_v2.adapters import (
    SupabaseTeacherProfileRepository,
    SupabaseWeeklyScheduleRepository,
)
from educational_planning_v2.models import TeacherProfile
from teacher_document_library_v2.adapters import SupabaseTeacherDocumentRepository
from portal_v2.authorization import (
    PORTAL_ROLE_TEACHER,
    SupabaseTrustedPortalRoleSource,
    build_portal_authorization_context,
)
from portal_v2.ui import render_admin_shell


PORTAL_PAGES = (
    "Tổng quan",
    "Lịch báo giảng",
    "Dữ liệu của tôi",
    "Kho tài liệu",
    "Chuẩn hóa Word",
    "Hồ sơ giáo viên",
)
PORTAL_SESSION_KEYS = (
    "portal_supabase_client",
    "portal_user_id",
    "portal_user_email",
    "portal_user_role",
    "portal_workspace",
    "admin_portal_page",
    "admin_portal_navigation",
    "portal_navigation",
    "weekly_supabase_client",
    "weekly_supabase_repository",
    "document_library_client",
    "document_library_repository",
    "google_drive_credentials",
    "google_oauth_url",
    "google_oauth_state",
)


def supabase_settings(
    environment: Mapping[str, str] | None = None,
) -> tuple[str, str] | None:
    values = os.environ if environment is None else environment
    url = values.get("SUPABASE_URL", "").strip()
    key = values.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
    return (url, key) if url and key else None


def create_supabase_client(url: str, publishable_key: str):
    from supabase import create_client

    return create_client(url, publishable_key)


def authenticate_portal(client: Any, email: str, password: str) -> tuple[str, str]:
    normalized_email = email.strip()
    if not normalized_email or not password:
        raise ValueError("Email và mật khẩu không được để trống.")
    response = client.auth.sign_in_with_password(
        {"email": normalized_email, "password": password}
    )
    user = getattr(response, "user", None)
    user_id = getattr(user, "id", None)
    if not user_id:
        raise ValueError("Supabase không trả về tài khoản giáo viên hợp lệ.")
    returned_email = str(getattr(user, "email", "") or normalized_email)
    return str(user_id), returned_email


def connect_feature_repositories(session_state: Any, client: Any, user_id: str) -> None:
    """Share one authenticated client across feature-specific adapters."""
    session_state["portal_supabase_client"] = client
    session_state["portal_user_id"] = user_id
    session_state["weekly_supabase_client"] = client
    session_state["weekly_supabase_repository"] = SupabaseWeeklyScheduleRepository(
        client, user_id
    )
    session_state["document_library_client"] = client
    session_state["document_library_repository"] = (
        SupabaseTeacherDocumentRepository(client, user_id)
    )


def clear_portal_session(session_state: Any) -> None:
    for key in PORTAL_SESSION_KEYS:
        session_state.pop(key, None)


def select_portal_page(session_state: Any, page: str) -> None:
    if page not in PORTAL_PAGES:
        raise ValueError("Trang cổng giáo viên không hợp lệ.")
    session_state["portal_page"] = page
    session_state["portal_navigation"] = page


def resolve_authenticated_portal_role(
    *,
    client: Any,
    user_id: str,
) -> str:
    """Resolve effective portal role from the trusted server-governed source."""
    source = SupabaseTrustedPortalRoleSource(
        client=client
    )
    resolution = source.resolve_role(
        user_id=user_id
    )
    return resolution.effective_role


def build_current_portal_authorization(session_state: Any):
    """Build UI authorization from authenticated session state."""
    return build_portal_authorization_context(
        user_id=str(session_state.get("portal_user_id", "")),
        email=str(session_state.get("portal_user_email", "")),
        role=str(
            session_state.get(
                "portal_user_role",
                PORTAL_ROLE_TEACHER,
            )
        ),
    )


def comma_values(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))


def build_teacher_profile(
    *, teacher_code: str, full_name: str, school_name: str,
    subjects: str, grade_levels: str, default_academic_year: str,
    show_teacher_name: bool, show_school_name: bool,
) -> TeacherProfile:
    return TeacherProfile(
        teacher_code=teacher_code,
        full_name=full_name,
        school_name=school_name,
        subjects=comma_values(subjects),
        grade_levels=comma_values(grade_levels),
        default_academic_year=default_academic_year,
        show_teacher_name=show_teacher_name,
        show_school_name=show_school_name,
    )


def render_login(st, settings: tuple[str, str] | None) -> None:
    st.title("MathTeacher-AI")
    st.subheader("Cổng làm việc dành cho giáo viên")
    st.caption("Một tài khoản · Một không gian · Các công cụ được kết nối")
    if settings is None:
        st.error("Chưa có SUPABASE_URL và SUPABASE_PUBLISHABLE_KEY.")
        st.info("Hãy cấu hình hai biến môi trường công khai rồi khởi động lại ứng dụng.")
        return
    with st.form("portal_login"):
        email = st.text_input("Email")
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
    if submitted:
        try:
            client = create_supabase_client(*settings)
            user_id, returned_email = authenticate_portal(client, email, password)
            connect_feature_repositories(st.session_state, client, user_id)
            st.session_state["portal_user_email"] = returned_email
            st.session_state["portal_user_role"] = (
                resolve_authenticated_portal_role(
                    client=client,
                    user_id=user_id,
                )
            )
            st.session_state["portal_page"] = "Tổng quan"
            st.rerun()
        except Exception as error:
            st.error(f"Không thể đăng nhập: {error}")


def render_dashboard(st) -> None:
    st.title("Tổng quan")
    st.caption("Chọn một công cụ để bắt đầu công việc.")
    cards = (
        ("Lịch báo giảng", "Tạo, lưu và xuất lịch dạy theo tuần."),
        (
            "Dữ liệu của tôi",
            "Quản lý PPCT, thời khóa biểu và tuần học theo năm học.",
        ),
        ("Kho tài liệu", "Tìm kiếm và tải tài liệu lên Google Drive."),
        ("Chuẩn hóa Word", "Chuẩn hóa giáo án Word mà không ghi đè bản gốc."),
        ("Hồ sơ giáo viên", "Quản lý thông tin dùng chung khi lập và xuất lịch."),
    )
    columns = st.columns(2)
    for index, (page, description) in enumerate(cards):
        with columns[index % 2].container(border=True):
            st.subheader(page)
            st.write(description)
            st.button(
                f"Mở {page}", key=f"open_{page}", use_container_width=True,
                on_click=select_portal_page, args=(st.session_state, page),
            )


def render_profile(st, client: Any, user_id: str) -> None:
    st.title("Hồ sơ giáo viên")
    st.caption("Thông tin này được dùng chung cho lịch báo giảng và tệp xuất.")
    repository = SupabaseTeacherProfileRepository(client, user_id)
    try:
        profile = repository.get()
    except Exception as error:
        st.error(f"Không thể đọc hồ sơ giáo viên: {error}")
        return
    with st.form("portal_teacher_profile"):
        teacher_code = st.text_input("Mã giáo viên *", value=profile.teacher_code if profile else "")
        full_name = st.text_input("Họ và tên *", value=profile.full_name if profile else "")
        school_name = st.text_input("Trường công tác *", value=profile.school_name if profile else "")
        subjects = st.text_input(
            "Môn giảng dạy *", value=", ".join(profile.subjects) if profile else "",
            help="Phân cách nhiều môn bằng dấu phẩy.",
        )
        grade_levels = st.text_input(
            "Khối/lớp phụ trách *", value=", ".join(profile.grade_levels) if profile else "",
            help="Phân cách nhiều khối bằng dấu phẩy.",
        )
        academic_year = st.text_input(
            "Năm học mặc định *", value=profile.default_academic_year if profile else "",
            placeholder="2026-2027",
        )
        show_teacher_name = st.checkbox(
            "Hiển thị họ tên trên lịch báo giảng",
            value=profile.show_teacher_name if profile else True,
        )
        show_school_name = st.checkbox(
            "Hiển thị trường trên lịch báo giảng",
            value=profile.show_school_name if profile else True,
        )
        submitted = st.form_submit_button("Lưu hồ sơ", use_container_width=True)
    if submitted:
        try:
            repository.save(build_teacher_profile(
                teacher_code=teacher_code, full_name=full_name,
                school_name=school_name, subjects=subjects,
                grade_levels=grade_levels, default_academic_year=academic_year,
                show_teacher_name=show_teacher_name,
                show_school_name=show_school_name,
            ))
            st.success("Đã lưu hồ sơ giáo viên.")
            st.rerun()
        except Exception as error:
            st.error(f"Không thể lưu hồ sơ: {error}")


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="MathTeacher-AI", page_icon="🎓", layout="wide")
    st.markdown("""
        <style>
        .block-container {max-width: 1240px; padding-top: 1.5rem;}
        [data-testid="stSidebar"] {border-right: 1px solid #e5e7eb;}
        </style>
    """, unsafe_allow_html=True)
    settings = supabase_settings()
    client = st.session_state.get("portal_supabase_client")
    user_id = st.session_state.get("portal_user_id")
    if client is None or not user_id:
        render_login(st, settings)
        return

    if st.query_params.get("code") or st.query_params.get("error"):
        select_portal_page(st.session_state, "Kho tài liệu")

    st.sidebar.title("MathTeacher-AI")
    st.sidebar.success("Đã đăng nhập")
    st.sidebar.caption(st.session_state.get("portal_user_email", "Giáo viên"))

    authorization = build_current_portal_authorization(
        st.session_state
    )

    workspace = "Gi?o vi?n"

    if authorization.can_access_admin_portal:
        workspace = st.sidebar.radio(
            "Khu v?c",
            ("Gi?o vi?n", "ADMIN"),
            key="portal_workspace",
            horizontal=True,
        )

    if workspace == "ADMIN":
        render_admin_shell(
            st,
            authorization,
        )
        return
    current_page = st.session_state.get("portal_page", "Tổng quan")
    if current_page not in PORTAL_PAGES:
        current_page = "Tổng quan"
    selected = st.sidebar.radio(
        "Công cụ", PORTAL_PAGES,
        index=PORTAL_PAGES.index(current_page),
        key="portal_navigation",
        label_visibility="collapsed",
    )
    st.session_state["portal_page"] = selected
    if st.sidebar.button("Đăng xuất", use_container_width=True):
        try:
            client.auth.sign_out()
        finally:
            clear_portal_session(st.session_state)
        st.rerun()

    if selected == "Tổng quan":
        render_dashboard(st)
    elif selected == "Lịch báo giảng":
        from portal_v2.ui.weekly_schedule_streamlit import (
            render_weekly_schedule_workspace,
        )
        render_weekly_schedule_workspace()

    elif selected == "Dữ liệu của tôi":
        from educational_planning_v2.models.teacher_operational_data_workspace import (
            TeacherOperationalDataWorkspace,
        )
        from portal_v2.ui.teacher_data_workspace_portal import (
            TeacherDataWorkspacePresenter,
        )
        from portal_v2.ui.teacher_data_workspace_streamlit import (
            render_teacher_data_workspace,
        )

        academic_year = st.text_input(
            "N\u0103m h\u1ecdc",
            key="teacher_data_academic_year",
            placeholder="V\u00ed d\u1ee5: 2026-2027",
        ).strip()

        if not academic_year:
            st.title("D\u1eef li\u1ec7u c\u1ee7a t\u00f4i")
            st.info(
                "Nh\u1eadp n\u0103m h\u1ecdc \u0111\u1ec3 xem "
                "v\u00e0 qu\u1ea3n l\u00fd d\u1eef li\u1ec7u."
            )
        else:
            workspace = TeacherOperationalDataWorkspace(
                owner_id=str(user_id),
                academic_year=academic_year,
            )

            view = TeacherDataWorkspacePresenter().present(
                workspace=workspace,
            )

            render_teacher_data_workspace(
                st=st,
                view=view,
            )

    elif selected == "Kho tài liệu":
        from scripts.document_library.app import main as render_document_library
        st.title("Kho tài liệu")
        render_document_library(embedded=True)
    elif selected == "Chuẩn hóa Word":
        from scripts.word_standardizer.app import main as render_word_standardizer
        st.title("Chuẩn hóa Word")
        render_word_standardizer(embedded=True)
    else:
        render_profile(st, client, str(user_id))


if __name__ == "__main__":
    main()

