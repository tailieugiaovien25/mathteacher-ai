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
from portal_v2.ui.user_registration_streamlit import render_user_registration
from portal_v2.ui.teacher_workspace_styles import apply_teacher_workspace_styles
from portal_v2.ui.modern_3d_design_system import (
    apply_modern_3d_design_system,
)


PORTAL_PAGES = (
    'T\u1ed5ng quan',
    'Chu\u1ea9n h\xf3a gi\xe1o \xe1n',
    'Qu\u1ea3n l\xfd gi\xe1o \xe1n',
    'So\u1ea1n b\xe0i c\xf9ng AI',
    'L\u1ecbch b\xe1o gi\u1ea3ng & PBSDTB',
    'Th\u1eddi kh\xf3a bi\u1ec3u',
    'D\u1eef li\u1ec7u c\u1ee7a t\xf4i',
    'Kho t\xe0i li\u1ec7u',
    'Thi\u1ebft \u0111\u1eb7t \u0111\u1ec1 ki\u1ec3m tra',
    'Ma tr\u1eadn & b\u1ea3n \u0111\u1eb7c t\u1ea3',
    'T\u1ea1o \u0111\u1ec1 ki\u1ec3m tra',
    'Xu\u1ea5t \u0111\u1ec1 ki\u1ec3m tra',
    'Thi\u1ebft \u0111\u1eb7t gi\xe1o vi\xean',
)

# The legacy authoring hub remains wired below for backward-compatible
# session/deep-link handling, but it is intentionally absent from the visible
# teacher navigation.  Its data contracts are consumed by the dedicated
# "Soạn bài cùng AI" and "Chuẩn hóa giáo án" pages.
PORTAL_SESSION_KEYS = (
    "portal_supabase_client",
    "portal_user_id",
    "portal_user_email",
    "portal_user_role",
    "portal_workspace",
    "portal_flash_feedback",
    "notification_repository",
    "operational_data_source_repository",
    "operational_payload_repository",
    "teacher_data_ppct_update_open",
    "teacher_data_ppct_view_open",
    "teacher_data_ppct_view_source_id",
    "teacher_timetable_catalog_snapshot",
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



def connect_document_library_runtime(
    session_state,
):
    """Build document-library services from the authenticated portal state."""

    repository = session_state.get(
        "document_library_repository"
    )

    if repository is None:
        return None

    from teacher_document_library_v2.services import (
        TeacherDocumentCatalog,
        TeacherDocumentUploadService,
    )

    catalog = TeacherDocumentCatalog(
        repository
    )

    session_state[
        "document_library_catalog"
    ] = catalog

    credential_payload = (
        session_state.get(
            "google_drive_credentials"
        )
    )

    if not credential_payload:
        session_state.pop(
            "document_library_storage",
            None,
        )
        session_state.pop(
            "document_library_upload_service",
            None,
        )
        return catalog

    from teacher_document_library_v2.adapters import (
        GoogleDriveFileStorage,
        credentials_from_dict,
    )

    credentials = credentials_from_dict(
        credential_payload
    )

    storage = GoogleDriveFileStorage(
        credentials
    )

    upload_service = (
        TeacherDocumentUploadService(
            catalog,
            storage,
        )
    )

    session_state[
        "document_library_storage"
    ] = storage

    session_state[
        "document_library_upload_service"
    ] = upload_service

    return catalog


def connect_feature_repositories(session_state: Any, client: Any, user_id: str) -> None:
    """Share one authenticated client across feature-specific adapters."""
    session_state["portal_supabase_client"] = client
    session_state["portal_user_id"] = user_id

    from lesson_planning_v2.adapters.supabase_lesson_plan_workspace_draft_repository import (
        SupabaseLessonPlanWorkspaceDraftRepository,
    )

    from notification_v2.adapters.supabase_notification_repository import (
        SupabaseNotificationRepository,
    )

    session_state[
        "lesson_plan_workspace_draft_repository"
    ] = (
        SupabaseLessonPlanWorkspaceDraftRepository(
            client=client,
        )
    )

    session_state["notification_repository"] = (
        SupabaseNotificationRepository(
            client=client,
            owner_id=user_id,
        )
    )

    from educational_planning_v2.adapters.supabase_operational_data_source_repository import (
        SupabaseOperationalDataSourceRepository,
    )
    from educational_planning_v2.adapters.supabase_operational_payload_repository import (
        SupabaseOperationalPayloadRepository,
    )

    session_state["operational_data_source_repository"] = (
        SupabaseOperationalDataSourceRepository(
            client=client,
            user_id=user_id,
        )
    )

    session_state["operational_payload_repository"] = (
        SupabaseOperationalPayloadRepository(
            client=client,
            user_id=user_id,
        )
    )

    session_state["weekly_supabase_client"] = client
    session_state["weekly_supabase_repository"] = SupabaseWeeklyScheduleRepository(
        client, user_id
    )
    session_state["document_library_client"] = client
    session_state["document_library_repository"] = (
        SupabaseTeacherDocumentRepository(client, user_id)
    )

    connect_document_library_runtime(
        session_state
    )


def clear_portal_session(session_state: Any) -> None:
    for key in PORTAL_SESSION_KEYS:
        session_state.pop(key, None)


def has_complete_portal_session(
    session_state: Any,
) -> bool:
    return bool(
        session_state.get(
            "portal_supabase_client"
        )
        and session_state.get(
            "portal_user_id"
        )
        and session_state.get(
            "portal_user_email"
        )
    )


def select_portal_page(session_state: Any, page: str) -> None:
    valid_pages = (*PORTAL_PAGES, "Công cụ soạn bài")
    if page not in valid_pages:
        raise ValueError("Trang cổng giáo viên không hợp lệ.")
    session_state["portal_page"] = page
    session_state["portal_navigation"] = page


def _autosave_before_portal_navigation(session_state: Any) -> None:
    """Keep working contexts intact and queue a floating page-change notice."""
    previous_page = str(session_state.get("portal_page", "Tổng quan") or "")
    next_page = str(session_state.get("portal_navigation", previous_page) or "")
    session_state["portal_navigation_autosave"] = {
        "previous_page": previous_page,
        "next_page": next_page,
        "lesson_context": dict(
            session_state.get("lesson_authoring_working_context", {}) or {}
        ),
        "timetable_draft": dict(
            session_state.get("teacher_timetable_autosaved_draft", {}) or {}
        ),
        "lbg_context": dict(
            session_state.get("lbg_autosaved_filter_context", {}) or {}
        ),
    }
    session_state["portal_navigation_notice"] = (
        f"Đã tự lưu dữ liệu trên trang {previous_page} trước khi chuyển trang."
    )


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

    if not resolution.can_access_portal:
        raise PermissionError(
            "Tài khoản chưa được kích hoạt hoặc đã ngừng hoạt động. "
            "Vui lòng liên hệ ADMIN."
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
    st.markdown(
        """
        <section class="mt-login-scene" aria-labelledby="mt-login-title">
          <div class="mt-login-brand">🎓 MathTeacher-AI</div>
          <h1 class="mt-login-title" id="mt-login-title">
            Không gian làm việc số dành cho giáo viên
          </h1>
          <p class="mt-login-lead">
            Soạn bài, chuẩn hóa giáo án, quản lý lịch dạy và tài liệu
            trong một hệ thống thống nhất, an toàn và thuận tiện.
          </p>
          <div class="mt-login-features" aria-label="Chức năng chính">
            <span class="mt-login-feature">✨ Soạn bài cùng AI</span>
            <span class="mt-login-feature">📝 Chuẩn hóa giáo án</span>
            <span class="mt-login-feature">📅 Lịch báo giảng</span>
            <span class="mt-login-feature">📚 Kho tài liệu</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if settings is None:
        st.error("Chưa có SUPABASE_URL và SUPABASE_PUBLISHABLE_KEY.")
        st.info("Hãy cấu hình hai biến môi trường công khai rồi khởi động lại ứng dụng.")
        return
    with st.form("portal_login"):
        email = st.text_input("Email")
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
    st.markdown(
        '<p class="mt-login-note">Một tài khoản · Một không gian · '
        'Các công cụ được kết nối</p>',
        unsafe_allow_html=True,
    )
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


    with st.expander("Chưa có tài khoản? Đăng ký sử dụng"):
        registration_client = create_supabase_client(*settings)
        render_user_registration(
            client=registration_client,
        )

def render_dashboard(st) -> None:
    st.title("Tổng quan")
    st.caption("Chọn một công cụ để bắt đầu công việc.")
    cards = (
        (
            'Công cụ soạn bài',
            'Ch\u1ecdn b\xe0i, so\u1ea1n c\xf9ng AI v\xe0 qu\u1ea3n l\xfd quy tr\xecnh so\u1ea1n b\xe0i.',
        ),
        (
            'Chuẩn hóa giáo án',
            'Ch\u1ecdn b\xe0i, so\u1ea1n c\xf9ng AI v\xe0 chu\u1ea9n h\xf3a gi\xe1o \xe1n.',
        ),
        (
            'D\u1eef li\u1ec7u c\u1ee7a t\xf4i',
            'Qu\u1ea3n l\xfd PPCT, th\u1eddi kh\xf3a bi\u1ec3u v\xe0 tu\u1ea7n h\u1ecdc theo n\u0103m h\u1ecdc.',
        ),
        (
            'Kho t\xe0i li\u1ec7u',
            'T\xecm ki\u1ebfm v\xe0 t\u1ea3i t\xe0i li\u1ec7u l\xean Google Drive.',
        ),
        (
            'Thi\u1ebft \u0111\u1eb7t gi\xe1o vi\xean',
            'Qu\u1ea3n l\xfd th\xf4ng tin, ph\xe2n c\xf4ng, nhi\u1ec7m v\u1ee5 v\xe0 thi\u1ebft \u0111\u1eb7t gi\xe1o \xe1n.',
        ),
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


def _render_teacher_information_settings(
    st,
    client: Any,
    user_id: str,
) -> None:
    st.subheader("Thông tin giáo viên")
    st.caption(
        "Th\u00f4ng tin n\u00e0y \u0111\u01b0\u1ee3c d\u00f9ng chung "
        "cho l\u1ecbch b\u00e1o gi\u1ea3ng v\u00e0 t\u1ec7p xu\u1ea5t."
    )

    repository = SupabaseTeacherProfileRepository(
        client,
        user_id,
    )

    try:
        profile = repository.get()
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            f"h\u1ed3 s\u01a1 gi\u00e1o vi\u00ean: {error}"
        )
        return

    with st.form("portal_teacher_profile"):
        teacher_code = st.text_input(
            "M\u00e3 gi\u00e1o vi\u00ean *",
            value=(
                profile.teacher_code
                if profile
                else ""
            ),
        )

        full_name = st.text_input(
            "H\u1ecd v\u00e0 t\u00ean *",
            value=(
                profile.full_name
                if profile
                else ""
            ),
        )

        school_name = st.text_input(
            "Tr\u01b0\u1eddng c\u00f4ng t\u00e1c *",
            value=(
                profile.school_name
                if profile
                else ""
            ),
        )

        subjects = st.text_input(
            "M\u00f4n gi\u1ea3ng d\u1ea1y *",
            value=(
                ", ".join(profile.subjects)
                if profile
                else ""
            ),
            help=(
                "Ph\u00e2n c\u00e1ch nhi\u1ec1u m\u00f4n "
                "b\u1eb1ng d\u1ea5u ph\u1ea9y."
            ),
        )

        grade_levels = st.text_input(
            "Kh\u1ed1i/l\u1edbp ph\u1ee5 tr\u00e1ch *",
            value=(
                ", ".join(profile.grade_levels)
                if profile
                else ""
            ),
            help=(
                "Ph\u00e2n c\u00e1ch nhi\u1ec1u kh\u1ed1i "
                "b\u1eb1ng d\u1ea5u ph\u1ea9y."
            ),
        )

        academic_year = st.text_input(
            "N\u0103m h\u1ecdc m\u1eb7c \u0111\u1ecbnh *",
            value=(
                profile.default_academic_year
                if profile
                else "2026-2027"
            ),
            placeholder="2026-2027",
        )

        show_teacher_name = st.checkbox(
            "Hi\u1ec3n th\u1ecb h\u1ecd t\u00ean "
            "tr\u00ean l\u1ecbch b\u00e1o gi\u1ea3ng",
            value=(
                profile.show_teacher_name
                if profile
                else True
            ),
        )

        show_school_name = st.checkbox(
            "Hi\u1ec3n th\u1ecb tr\u01b0\u1eddng "
            "tr\u00ean l\u1ecbch b\u00e1o gi\u1ea3ng",
            value=(
                profile.show_school_name
                if profile
                else True
            ),
        )

        submitted = st.form_submit_button(
            "L\u01b0u h\u1ed3 s\u01a1",
            use_container_width=True,
        )

    if submitted:
        try:
            repository.save(
                build_teacher_profile(
                    teacher_code=teacher_code,
                    full_name=full_name,
                    school_name=school_name,
                    subjects=subjects,
                    grade_levels=grade_levels,
                    default_academic_year=academic_year,
                    show_teacher_name=show_teacher_name,
                    show_school_name=show_school_name,
                )
            )

            from portal_v2.ui.portal_flash_feedback import (
                PortalFlashLevel,
                set_portal_flash,
            )

            set_portal_flash(
                st.session_state,
                message=(
                    "\u0110\u00e3 l\u01b0u h\u1ed3 s\u01a1 "
                    "gi\u00e1o vi\u00ean th\u00e0nh c\u00f4ng."
                ),
                level=PortalFlashLevel.SUCCESS,
            )

            st.rerun()

        except Exception as error:
            st.error(
                f"Kh\u00f4ng th\u1ec3 l\u01b0u "
                f"h\u1ed3 s\u01a1: {error}"
            )


def _render_teacher_assignment_settings(
    st,
    client: Any,
    user_id: str,
    academic_year: str,
) -> None:
    from educational_planning_v2.adapters.supabase_class_catalog_repository import (
        SupabaseClassCatalogRepository,
    )
    from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
        SupabaseSubjectCatalogRepository,
    )
    from educational_planning_v2.adapters.supabase_teaching_assignment_repository import (
        SupabaseTeachingAssignmentRepository,
    )
    from educational_planning_v2.models.teaching_assignment import (
        TeachingAssignmentRole,
        TeachingAssignmentStatus,
    )

    st.subheader("Phân công và nhiệm vụ")
    st.caption(
        "Danh sách được lấy từ phân công chuyên môn đang hiệu lực "
        "của giáo viên. Việc thay đổi phân công do quản trị viên thực hiện."
    )

    try:
        assignments = (
            SupabaseTeachingAssignmentRepository(
                client=client,
                user_id=user_id,
            )
            .list_assignments(
                owner_id=user_id,
                academic_year=academic_year,
                role=TeachingAssignmentRole.TEACHING,
                status=TeachingAssignmentStatus.ACTIVE,
            )
        )
    except Exception as error:
        st.error(f"Không thể đọc phân công và nhiệm vụ: {error}")
        return

    if not assignments:
        st.info(
            f"Chưa có phân công chuyên môn đang hiệu lực "
            f"cho năm học {academic_year}."
        )
        return

    class_repository = SupabaseClassCatalogRepository(
        client=client,
    )
    subject_repository = SupabaseSubjectCatalogRepository(
        client=client,
    )
    rows = []

    for assignment in assignments:
        class_name = "Chưa xác định"
        subject_name = "Chưa xác định"
        component_name = ""

        try:
            class_item = class_repository.get(
                class_id=assignment.class_id,
            )
            if class_item is not None:
                class_name = str(
                    class_item.display_name
                ).strip() or class_name
        except Exception:
            pass

        try:
            subject_item = subject_repository.get_subject(
                subject_id=assignment.subject_ref,
            )
            if subject_item is not None:
                subject_name = str(
                    subject_item.name
                ).strip() or subject_name
        except Exception:
            pass

        if assignment.component_ref:
            try:
                component_item = subject_repository.get_component(
                    component_id=assignment.component_ref,
                )
                if component_item is not None:
                    component_name = str(
                        component_item.name
                    ).strip()
            except Exception:
                pass

        rows.append(
            {
                "Lớp": class_name,
                "Môn": subject_name,
                "Phân môn": component_name or "—",
                "Nhiệm vụ": "Giảng dạy",
                "Năm học": academic_year,
                "Trạng thái": "Đang hiệu lực",
            }
        )

    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
    )
    st.caption(
        f"Tổng số phân công đang hiệu lực: {len(rows)}"
    )


def render_teacher_settings(
    st,
    client: Any,
    user_id: str,
) -> None:
    st.title("Thiết đặt giáo viên")
    st.caption(
        "Quản lý tập trung thông tin giáo viên, nhiệm vụ được giao "
        "và các thông số kỹ thuật dùng khi tạo giáo án."
    )

    try:
        profile = SupabaseTeacherProfileRepository(
            client,
            user_id,
        ).get()
    except Exception:
        profile = None

    from educational_planning_v2.models.academic_year_configuration import (
        normalize_academic_year,
    )

    academic_year = ""

    try:
        from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
            SupabaseAcademicYearConfigurationRepository,
        )

        current_year = (
            SupabaseAcademicYearConfigurationRepository(
                client=client,
            )
            .get_current()
        )
        if current_year is not None:
            academic_year = current_year.academic_year
    except Exception:
        academic_year = ""

    if not academic_year and profile and profile.default_academic_year:
        try:
            academic_year = normalize_academic_year(
                str(profile.default_academic_year)
            )
        except (TypeError, ValueError):
            academic_year = ""

    if not academic_year:
        st.warning(
            "Chưa xác định được năm học hiện hành. "
            "Vui lòng liên hệ ADMIN để cấu hình năm học."
        )
        return

    information_tab, assignment_tab, lesson_plan_tab = st.tabs(
        (
            "1. Thông tin giáo viên",
            "2. Phân công và nhiệm vụ",
            "3. Thiết đặt giáo án (Mẫu giáo án)",
        )
    )

    with information_tab:
        _render_teacher_information_settings(
            st,
            client,
            user_id,
        )

    with assignment_tab:
        _render_teacher_assignment_settings(
            st,
            client,
            user_id,
            academic_year,
        )

    with lesson_plan_tab:
        from portal_v2.ui.lesson_plan_template_setup_streamlit import (
            render_lesson_plan_template_setup,
        )

        render_lesson_plan_template_setup(
            client=client,
            teacher_id=str(user_id),
            academic_year=academic_year,
            embedded=True,
        )


def render_profile(st, client: Any, user_id: str) -> None:
    """Backward-compatible alias for the unified settings page."""
    render_teacher_settings(st, client, user_id)



def main() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="MathTeacher-AI",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_teacher_workspace_styles(st)
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
          background:#071a33 !important;
        }
        [data-testid="stSidebar"] * {
          color:#ffffff !important;
          font-size:18px !important;
          line-height:1.5 !important;
        }
        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="collapsedControl"] button {
          background:#071a33 !important;
          color:#ffffff !important;
          border:1px solid #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Load the modern layer last so legacy page-specific rules cannot
    # override the shared visual contract.
    apply_modern_3d_design_system(st)
    settings = supabase_settings()
    client = st.session_state.get("portal_supabase_client")
    user_id = st.session_state.get("portal_user_id")

    if not has_complete_portal_session(
        st.session_state
    ):
        clear_portal_session(
            st.session_state
        )
        render_login(
            st,
            settings,
        )
        return

    # Rebind feature adapters on every authenticated rerun.
    # Streamlit can retain old Python objects in session_state
    # across source-code hot reloads.
    connect_feature_repositories(
        st.session_state,
        client,
        str(user_id),
    )

    if st.query_params.get("code") or st.query_params.get("error"):
        select_portal_page(st.session_state, "Kho tài liệu")

    st.sidebar.title("MathTeacher-AI")
    st.sidebar.success("Đã đăng nhập")
    st.sidebar.caption(st.session_state.get("portal_user_email", "Giáo viên"))

    from portal_v2.ui.portal_flash_feedback import (
        render_portal_flash,
    )

    render_portal_flash(
        st=st,
        session_state=st.session_state,
    )

    notification_repository = (
        st.session_state.get(
            "notification_repository"
        )
    )

    if notification_repository is not None:
        try:
            from notification_v2.services import (
                NotificationService,
            )
            from portal_v2.ui.notification_center_presenter import (
                build_notification_center_view,
            )
            from portal_v2.ui.notification_center_streamlit import (
                render_notification_center_sidebar,
            )

            notification_service = NotificationService(
                repository=notification_repository,
            )

            notifications = (
                notification_service.list_for_owner(
                    owner_id=str(user_id),
                    limit=20,
                )
            )

            unread_count = (
                notification_service.count_unread(
                    owner_id=str(user_id),
                )
            )

            notification_view = (
                build_notification_center_view(
                    notifications=notifications,
                    unread_count=unread_count,
                )
            )

            def handle_notification_mark_read(
                notification_id: str,
            ) -> None:
                notification_service.mark_read(
                    notification_id=notification_id,
                    owner_id=str(user_id),
                )

            def handle_notification_mark_all_read() -> None:
                notification_service.mark_all_read(
                    owner_id=str(user_id),
                )

            render_notification_center_sidebar(
                st=st,
                view=notification_view,
                on_mark_read=(
                    handle_notification_mark_read
                ),
                on_mark_all_read=(
                    handle_notification_mark_all_read
                ),
            )

        except Exception:
            st.sidebar.caption(
                "Th\u00f4ng b\u00e1o t\u1ea1m th\u1eddi "
                "ch\u01b0a kh\u1ea3 d\u1ee5ng."
            )

    authorization = build_current_portal_authorization(
        st.session_state
    )

    workspace = "Giáo viên"

    if authorization.can_access_admin_portal:
        workspace = st.sidebar.radio(
            "Khu vực",
            ("Giáo viên", "ADMIN"),
            key="portal_workspace",
            horizontal=True,
        )

    if workspace == "ADMIN":
        render_admin_shell(
            st,
            authorization,
            client=client,
        )
        return
    current_page = st.session_state.get("portal_page", "Tổng quan")
    hidden_legacy_page = current_page == "Công cụ soạn bài"
    if current_page not in PORTAL_PAGES and not hidden_legacy_page:
        current_page = "Tổng quan"
    if hidden_legacy_page:
        selected = current_page
    else:
        selected = st.sidebar.radio(
            "Công cụ", PORTAL_PAGES,
            index=PORTAL_PAGES.index(current_page),
            key="portal_navigation",
            label_visibility="collapsed",
            on_change=_autosave_before_portal_navigation,
            args=(st.session_state,),
        )
    st.session_state["portal_page"] = selected
    navigation_notice = st.session_state.pop("portal_navigation_notice", "")
    if navigation_notice:
        st.toast(str(navigation_notice))
    if st.sidebar.button("Đăng xuất", use_container_width=True):
        try:
            client.auth.sign_out()
        finally:
            clear_portal_session(st.session_state)
        st.rerun()

    if selected == "Tổng quan":
        render_dashboard(st)

    elif selected == 'Công cụ soạn bài':
        from portal_v2.ui.weekly_schedule_streamlit import (
            render_lesson_authoring_tools_workspace,
        )

        render_lesson_authoring_tools_workspace(
            client=client,
            user_id=str(user_id),
        )

    elif selected == 'Chu\u1ea9n h\xf3a gi\xe1o \xe1n':
        from portal_v2.ui.weekly_schedule_streamlit import (
            render_weekly_schedule_workspace,
        )
        render_weekly_schedule_workspace(
            client=client,
            user_id=str(user_id),
            compact_setup_ui=False,
        )



    elif selected == 'Qu\u1ea3n l\xfd gi\xe1o \xe1n':
        from portal_v2.ui.weekly_schedule_streamlit import (
            render_lesson_plan_management_workspace,
        )

        render_lesson_plan_management_workspace(
            client=client,
            user_id=str(user_id),
        )

    elif selected == 'So\u1ea1n b\xe0i c\xf9ng AI':
        from portal_v2.ui.lesson_authoring_ai_streamlit import (
            render_lesson_authoring_ai_page,
        )

        render_lesson_authoring_ai_page(
            client=client,
            user_id=str(user_id),
        )

    elif selected == 'L\u1ecbch b\xe1o gi\u1ea3ng & PBSDTB':
        from portal_v2.ui.weekly_schedule_streamlit import (
            render_weekly_schedule_and_equipment_workspace,
        )

        render_weekly_schedule_and_equipment_workspace(
            client=client,
            user_id=str(user_id),
        )


    elif selected == "Thời khóa biểu":
        from portal_v2.ui.teacher_timetable_streamlit import (
            render_teacher_timetable,
        )

        render_teacher_timetable(
            st=st,
            client=client,
            user_id=str(user_id),
        )

    elif selected == "Dữ liệu của tôi":
        from educational_planning_v2.services.teacher_operational_data_workspace_service import (
            TeacherOperationalDataWorkspaceRequest,
            TeacherOperationalDataWorkspaceService,
        )
        from portal_v2.ui.teacher_data_workspace_portal import (
            TeacherDataWorkspacePresenter,
        )
        from portal_v2.ui.teacher_data_workspace_streamlit import (
            render_teacher_data_workspace,
        )

        from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
            SupabaseAcademicYearConfigurationRepository,
        )

        try:
            admin_current_year = (
                SupabaseAcademicYearConfigurationRepository(
                    client=client,
                )
                .get_current()
            )
        except Exception as error:
            st.title("Dữ liệu của tôi")
            st.error(f"Không thể đọc năm học hiện hành: {error}")
            return

        if admin_current_year is None:
            st.title("Dữ liệu của tôi")
            st.warning("ADMIN ch\u01b0a thi\u1ebft l\u1eadp n\u0103m h\u1ecdc hi\u1ec7n h\u00e0nh.")
            return

        academic_year = str(admin_current_year.academic_year)
        # Legacy source contract: key="teacher_data_academic_year"
        st.session_state["teacher_data_academic_year"] = academic_year
        st.text_input(
            "Năm học",
            value=academic_year,
            key="teacher_data_academic_year_display",
            disabled=True,
        )
        st.caption("N\u0103m h\u1ecdc do ADMIN thi\u1ebft l\u1eadp.")

        if academic_year:
            repository = st.session_state.get(
                "operational_data_source_repository"
            )

            if repository is None:
                st.error(
                    "Kho d\u1eef li\u1ec7u v\u1eadn h\u00e0nh "
                    "ch\u01b0a s\u1eb5n s\u00e0ng. "
                    "H\u00e3y \u0111\u0103ng nh\u1eadp l\u1ea1i."
                )
                return

            workspace = TeacherOperationalDataWorkspaceService(
                repository
            ).build(
                request=TeacherOperationalDataWorkspaceRequest(
                    owner_id=str(user_id),
                    academic_year=academic_year,
                )
            )

            view = TeacherDataWorkspacePresenter().present(
                workspace=workspace,
            )

            def handle_ppct_update() -> None:
                st.session_state[
                    "teacher_data_ppct_update_open"
                ] = True

            render_teacher_data_workspace(
                st=st,
                view=view,
                on_ppct_update=handle_ppct_update,
            )

            if st.session_state.get(
                "teacher_data_ppct_update_open",
                False,
            ):
                from uuid import uuid4

                from educational_planning_v2.services.ppct_import_service import (
                    PPCTImportRequest,
                    PPCTImportService,
                )

                st.subheader(
                    "C\u1eadp nh\u1eadt ph\u00e2n ph\u1ed1i "
                    "ch\u01b0\u01a1ng tr\u00ecnh"
                )

                from educational_planning_v2.adapters.ppct_template_workbook_adapter import (
                    PPCTTemplateWorkbookAdapter,
                )
                from educational_planning_v2.adapters.ppct_workbook_upload_adapter import (
                    PPCTWorkbookUploadAdapter,
                )

                template_bytes = (
                    PPCTTemplateWorkbookAdapter()
                    .build()
                )

                st.download_button(
                    "T\u1ea3i file PPCT m\u1eabu",
                    data=template_bytes,
                    file_name="MathTeacherAI_PPCT_Template_V1.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.spreadsheetml.sheet"
                    ),
                    key="teacher_data_ppct_template_download",
                    use_container_width=True,
                )

                uploaded_ppct = st.file_uploader(
                    "Ch\u1ecdn t\u1ec7p PPCT Excel",
                    type=("xlsx",),
                    key="teacher_data_ppct_upload",
                    help=(
                        "Ch\u1ecdn t\u1ec7p Excel ch\u1ee9a "
                        "ph\u00e2n ph\u1ed1i ch\u01b0\u01a1ng "
                        "tr\u00ecnh c\u1ee7a n\u0103m h\u1ecdc "
                        "\u0111ang m\u1edf."
                    ),
                )

                if uploaded_ppct is None:
                    st.info(
                        "Ch\u1ecdn t\u1ec7p Excel \u0111\u1ec3 "
                        "chu\u1ea9n b\u1ecb nh\u1eadp "
                        "d\u1eef li\u1ec7u PPCT."
                    )
                else:
                    st.success(
                        "\u0110\u00e3 nh\u1eadn t\u1ec7p: "
                        f"{uploaded_ppct.name}"
                    )

                    ppct_preview_rows = None
                    ppct_preview_error = None

                    try:
                        ppct_preview_rows = (
                            PPCTWorkbookUploadAdapter()
                            .parse(
                                workbook_bytes=uploaded_ppct.getvalue(),
                            )
                        )
                    except Exception as error:
                        ppct_preview_error = str(error)

                    if ppct_preview_error is not None:
                        st.error(
                            "T\u1ec7p PPCT ch\u01b0a h\u1ee3p l\u1ec7: "
                            f"{ppct_preview_error}"
                        )
                    else:
                        st.success(
                            "Ki\u1ec3m tra c\u1ea5u tr\u00fac PPCT: "
                            "H\u1ee2P L\u1ec6"
                        )

                        preview_data = [
                            {
                                "M\u00f4n/L\u1edbp": row.subject_grade,
                                "Ph\u00e2n m\u00f4n": (
                                    row.sub_subject or ""
                                ),
                                "Ti\u1ebft": row.period,
                                "T\u00ean b\u00e0i h\u1ecdc": row.lesson_name,
                            }
                            for row in ppct_preview_rows[:20]
                        ]

                        st.caption(
                            "Xem tr\u01b0\u1edbc t\u1ed1i \u0111a "
                            "20 d\u00f2ng \u0111\u1ea7u."
                        )

                        st.dataframe(
                            preview_data,
                            use_container_width=True,
                            hide_index=True,
                        )

                    source_repository = st.session_state.get(
                        "operational_data_source_repository"
                    )

                    payload_repository = st.session_state.get(
                        "operational_payload_repository"
                    )

                    if (
                        source_repository is None
                        or payload_repository is None
                    ):
                        st.error(
                            "Kho d\u1eef li\u1ec7u "
                            "ch\u01b0a s\u1eb5n s\u00e0ng. "
                            "H\u00e3y \u0111\u0103ng nh\u1eadp l\u1ea1i."
                        )
                    else:
                        if st.button(
                            "Nh\u1eadp PPCT v\u00e0o h\u1ec7 th\u1ed1ng",
                            key="teacher_data_ppct_import",
                            type="primary",
                            use_container_width=True,
                            disabled=(
                                ppct_preview_error is not None
                                or not ppct_preview_rows
                            ),
                        ):
                            try:
                                source_id = (
                                    "ppct-"
                                    + academic_year.replace(
                                        " ",
                                        "",
                                    )
                                    + "-"
                                    + uuid4().hex
                                )

                                service = PPCTImportService(
                                    source_repository=source_repository,
                                    payload_repository=payload_repository,
                                )

                                result = service.import_workbook(
                                    request=PPCTImportRequest(
                                        owner_id=str(user_id),
                                        academic_year=academic_year,
                                        source_id=source_id,
                                        source_name=uploaded_ppct.name,
                                        source_version="1",
                                    ),
                                    workbook_bytes=uploaded_ppct.getvalue(),
                                )

                                st.session_state[
                                    "teacher_data_ppct_update_open"
                                ] = False

                                st.session_state[
                                    "teacher_data_ppct_view_open"
                                ] = True

                                st.session_state[
                                    "teacher_data_ppct_view_source_id"
                                ] = result.source.source_id

                                from portal_v2.ui.portal_flash_feedback import (
                                    PortalFlashLevel,
                                    set_portal_flash,
                                )

                                set_portal_flash(
                                    st.session_state,
                                    message=(
                                        "\u0110\u00e3 c\u1eadp nh\u1eadt "
                                        "d\u1eef li\u1ec7u PPCT "
                                        "th\u00e0nh c\u00f4ng."
                                    ),
                                    level=PortalFlashLevel.SUCCESS,
                                )

                                st.rerun()

                            except Exception as error:
                                st.error(
                                    "Kh\u00f4ng th\u1ec3 nh\u1eadp PPCT: "
                                    f"{error}"
                                )

            if st.session_state.get(
                "teacher_data_ppct_view_open",
                False,
            ):
                from educational_planning_v2.models.operational_data_source import (
                    OperationalDataType,
                )
                from educational_planning_v2.models.operational_payload import (
                    OperationalPayloadReference,
                )

                ppct_source_id = st.session_state.get(
                    "teacher_data_ppct_view_source_id"
                )

                payload_repository = st.session_state.get(
                    "operational_payload_repository"
                )

                source_repository = st.session_state.get(
                    "operational_data_source_repository"
                )

                def render_persisted_ppct_view() -> None:
                    if (
                        source_repository is None
                        or payload_repository is None
                        or not ppct_source_id
                    ):
                        st.error(
                            "Kh\u00f4ng th\u1ec3 m\u1edf "
                            "d\u1eef li\u1ec7u PPCT."
                        )
                        return

                    source = source_repository.get(
                        source_id=ppct_source_id,
                    )

                    if source is None:
                        st.error(
                            "Kh\u00f4ng t\u00ecm th\u1ea5y "
                            "ngu\u1ed3n PPCT."
                        )
                        return

                    envelope = payload_repository.get(
                        reference=OperationalPayloadReference(
                            source_id=source.source_id,
                            data_type=OperationalDataType.PPCT,
                            payload_version=source.source_version,
                        )
                    )

                    if envelope is None:
                        st.error(
                            "Kh\u00f4ng t\u00ecm th\u1ea5y "
                            "payload PPCT."
                        )
                        return

                    st.caption(
                        f"N\u0103m h\u1ecdc: "
                        f"{source.academic_year}"
                    )

                    st.write(
                        f"Ngu\u1ed3n: "
                        f"{source.source_name or source.source_id}"
                    )

                    st.write(
                        f"Phi\u00ean b\u1ea3n: "
                        f"{source.source_version or '\u2014'}"
                    )

                    st.write(
                        f"Tr\u1ea1ng th\u00e1i: "
                        f"{source.status.value}"
                    )

                    rows = list(
                        envelope.payload
                    )

                    st.write(
                        f"T\u1ed5ng s\u1ed1 d\u00f2ng: "
                        f"{len(rows)}"
                    )

                    table_rows = [
                        {
                            "M\u00f4n/L\u1edbp": row.get(
                                "subject_grade",
                                "",
                            ),
                            "Ph\u00e2n m\u00f4n": (
                                row.get(
                                    "sub_subject",
                                    "",
                                )
                                or ""
                            ),
                            "Ti\u1ebft": row.get(
                                "period",
                                "",
                            ),
                            "T\u00ean b\u00e0i h\u1ecdc": row.get(
                                "lesson_name",
                                "",
                            ),
                        }
                        for row in rows
                    ]

                    st.dataframe(
                        table_rows,
                        use_container_width=True,
                        hide_index=True,
                    )

                    left, right = st.columns(2)

                    with left:
                        if st.button(
                            "\u0110\u00f3ng",
                            key="teacher_data_ppct_view_close",
                            use_container_width=True,
                        ):
                            st.session_state[
                                "teacher_data_ppct_view_open"
                            ] = False
                            st.rerun()

                    with right:
                        if st.button(
                            "C\u1eadp nh\u1eadt l\u1ea1i PPCT",
                            key="teacher_data_ppct_view_update",
                            use_container_width=True,
                        ):
                            st.session_state[
                                "teacher_data_ppct_view_open"
                            ] = False
                            st.session_state[
                                "teacher_data_ppct_update_open"
                            ] = True
                            st.rerun()

                if callable(
                    getattr(
                        st,
                        "dialog",
                        None,
                    )
                ):
                    @st.dialog(
                        "PPCT \u0111\u00e3 nh\u1eadp",
                        width="large",
                    )
                    def ppct_dialog():
                        render_persisted_ppct_view()

                    ppct_dialog()

                else:
                    with st.container(
                        border=True
                    ):
                        st.subheader(
                            "PPCT \u0111\u00e3 nh\u1eadp"
                        )
                        render_persisted_ppct_view()

    elif selected == "Thiết đặt đề kiểm tra":
        from portal_v2.ui.assessment_exam_settings_streamlit import (
            render_assessment_exam_settings_page,
        )

        render_assessment_exam_settings_page(
            st=st,
            client=client,
            user_id=str(user_id),
        )

    elif selected == "Ma trận & bản đặc tả":
        from portal_v2.ui.assessment_blueprint_authoring_streamlit import (
            render_assessment_blueprint_authoring_page,
        )

        render_assessment_blueprint_authoring_page(
            st=st,
            client=client,
            user_id=str(user_id),
        )

    elif selected == "Tạo đề kiểm tra":
        from portal_v2.ui.assessment_exam_generation_streamlit import (
            render_assessment_exam_generation_page,
        )

        render_assessment_exam_generation_page(
            st=st,
            client=client,
            user_id=str(user_id),
        )

    elif selected == "Xuất đề kiểm tra":
        from portal_v2.ui.assessment_document_export_streamlit import (
            render_assessment_document_export_page,
        )

        render_assessment_document_export_page(
            st=st,
            client=client,
            user_id=str(user_id),
        )

    elif selected == "Thiết đặt giáo viên":
        render_teacher_settings(
            st,
            client,
            str(user_id),
        )

    elif selected == "Kho tài liệu":
        from scripts.document_library.app import main as render_document_library
        st.title("Kho tài liệu")
        render_document_library(embedded=True)


if __name__ == "__main__":
    main()

