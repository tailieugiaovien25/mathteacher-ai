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
    "T\u1ed5ng quan",
    "L\u1ecbch b\u00e1o gi\u1ea3ng",
    "Th\u1eddi kh\u00f3a bi\u1ec3u",
    "\u0110\u0103ng k\u00fd m\u00f4n/ph\u00e2n m\u00f4n",
    "D\u1eef li\u1ec7u c\u1ee7a t\u00f4i",
    "Kho t\u00e0i li\u1ec7u",
    "Chu\u1ea9n h\u00f3a Word",
    "H\u1ed3 s\u01a1 gi\u00e1o vi\u00ean",
)
PORTAL_SESSION_KEYS = (
    "portal_supabase_client",
    "portal_user_id",
    "portal_user_email",
    "portal_user_role",
    "portal_workspace",
    "operational_data_source_repository",
    "operational_payload_repository",
    "teacher_data_ppct_update_open",
    "teacher_data_ppct_view_open",
    "teacher_data_ppct_view_source_id",
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
    from dataclasses import replace
    from datetime import date
    from uuid import uuid4

    from educational_planning_v2.adapters.supabase_teaching_assignment_repository import (
        SupabaseTeachingAssignmentRepository,
    )
    from educational_planning_v2.models.teaching_assignment import (
        TeachingAssignment,
        TeachingAssignmentRole,
        TeachingAssignmentStatus,
    )
    from educational_planning_v2.services.teaching_assignment_legacy_migration_service import (
        TeachingAssignmentLegacyMigrationService,
    )

    st.title("H\u1ed3 s\u01a1 gi\u00e1o vi\u00ean")
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
                else ""
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

            st.success(
                "\u0110\u00e3 l\u01b0u h\u1ed3 s\u01a1 "
                "gi\u00e1o vi\u00ean."
            )

            st.rerun()

        except Exception as error:
            st.error(
                f"Kh\u00f4ng th\u1ec3 l\u01b0u "
                f"h\u1ed3 s\u01a1: {error}"
            )

    st.divider()

    st.subheader(
        "Ph\u00e2n c\u00f4ng gi\u1ea3ng d\u1ea1y"
    )

    assignment_repository = (
        SupabaseTeachingAssignmentRepository(
            client,
            user_id,
        )
    )

    assignment_year = (
        profile.default_academic_year
        if profile is not None
        else academic_year.strip()
    )

    if not assignment_year:
        st.info(
            "H\u00e3y l\u01b0u N\u0103m h\u1ecdc "
            "m\u1eb7c \u0111\u1ecbnh tr\u01b0\u1edbc."
        )
        return

    st.caption(
        f"N\u0103m h\u1ecdc: {assignment_year}"
    )

    st.info(
        "M\u1ed7i d\u00f2ng ph\u00e2n c\u00f4ng = "
        "1 L\u1edbp + 1 M\u00f4n + 0/1 Ph\u00e2n m\u00f4n. "
        "N\u1ebfu d\u1ea1y nhi\u1ec1u m\u00f4n ho\u1eb7c "
        "nhi\u1ec1u ph\u00e2n m\u00f4n tr\u00ean c\u00f9ng "
        "m\u1ed9t l\u1edbp, h\u00e3y th\u00eam nhi\u1ec1u "
        "d\u00f2ng ph\u00e2n c\u00f4ng."
    )

    with st.form(
        "portal_teaching_assignment_add"
    ):
        role_label = st.selectbox(
            "Vai tr\u00f2 *",
            (
                "Gi\u1ea3ng d\u1ea1y",
                "Ch\u1ee7 nhi\u1ec7m",
            ),
        )

        is_homeroom = (
            role_label == "Ch\u1ee7 nhi\u1ec7m"
        )

        other_label = "Kh\u00e1c..."

        known_classes = (
            tuple(profile.grade_levels)
            if profile is not None
            else ()
        )

        class_options = (
            ("",)
            + known_classes
            + (other_label,)
        )

        class_choice = st.selectbox(
            "L\u1edbp *",
            options=class_options,
            help=(
                "M\u1ed7i ph\u00e2n c\u00f4ng "
                "ch\u1ec9 ch\u1ecdn m\u1ed9t l\u1edbp."
            ),
        )

        if class_choice == other_label:
            class_id = st.text_input(
                "Nh\u1eadp l\u1edbp kh\u00e1c *",
                placeholder="V\u00ed d\u1ee5: 6A2",
            )
        else:
            class_id = class_choice

        known_subjects = (
            tuple(profile.subjects)
            if profile is not None
            else ()
        )

        subject_options = (
            ("",)
            + known_subjects
            + (other_label,)
        )

        if is_homeroom:
            subject_ref = ""
            st.text_input(
                "M\u00f4n",
                value="",
                disabled=True,
                help=(
                    "Ph\u00e2n c\u00f4ng ch\u1ee7 nhi\u1ec7m "
                    "kh\u00f4ng b\u1eaft bu\u1ed9c c\u00f3 m\u00f4n."
                ),
            )
        else:
            subject_choice = st.selectbox(
                "M\u00f4n *",
                options=subject_options,
                help=(
                    "M\u1ed7i ph\u00e2n c\u00f4ng "
                    "ch\u1ec9 ch\u1ecdn m\u1ed9t m\u00f4n."
                ),
            )

            if subject_choice == other_label:
                subject_ref = st.text_input(
                    "Nh\u1eadp m\u00f4n kh\u00e1c *",
                    placeholder="V\u00ed d\u1ee5: To\u00e1n",
                )
            else:
                subject_ref = subject_choice

        component_ref = st.text_input(
            "Ph\u00e2n m\u00f4n",
            placeholder=(
                "V\u00ed d\u1ee5: S\u1ed1 h\u1ecdc, "
                "H\u00ecnh h\u1ecdc..."
            ),
            disabled=is_homeroom,
        )

        date_columns = st.columns(2)

        with date_columns[0]:
            effective_from = st.date_input(
                "T\u1eeb ng\u00e0y *",
                value=date.today(),
            )

        with date_columns[1]:
            effective_to = st.date_input(
                "\u0110\u1ebfn ng\u00e0y *",
                value=date.today(),
            )

        add_assignment = st.form_submit_button(
            "Th\u00eam ph\u00e2n c\u00f4ng",
            type="primary",
            use_container_width=True,
        )

    if add_assignment:
        try:
            if "," in class_id or ";" in class_id:
                raise ValueError(
                    "M\u1ed7i ph\u00e2n c\u00f4ng ch\u1ec9 \u0111\u01b0\u1ee3c ch\u1ecdn m\u1ed9t l\u1edbp. "
                    "H\u00e3y t\u1ea1o th\u00eam ph\u00e2n c\u00f4ng cho l\u1edbp kh\u00e1c."
                )

            if (
                not is_homeroom
                and (
                    "," in subject_ref
                    or ";" in subject_ref
                )
            ):
                raise ValueError(
                    "M\u1ed7i ph\u00e2n c\u00f4ng ch\u1ec9 \u0111\u01b0\u1ee3c ch\u1ecdn m\u1ed9t m\u00f4n. "
                    "H\u00e3y t\u1ea1o th\u00eam ph\u00e2n c\u00f4ng cho m\u00f4n kh\u00e1c."
                )

            if (
                not is_homeroom
                and (
                    "," in component_ref
                    or ";" in component_ref
                )
            ):
                raise ValueError(
                    "M\u1ed7i ph\u00e2n c\u00f4ng ch\u1ec9 \u0111\u01b0\u1ee3c ch\u1ecdn m\u1ed9t ph\u00e2n m\u00f4n. "
                    "H\u00e3y t\u1ea1o th\u00eam ph\u00e2n c\u00f4ng cho ph\u00e2n m\u00f4n kh\u00e1c."
                )

            role = (
                TeachingAssignmentRole.HOMEROOM
                if is_homeroom
                else TeachingAssignmentRole.TEACHING
            )

            assignment_repository.save(
                assignment=TeachingAssignment(
                    assignment_id=(
                        "assign-"
                        + uuid4().hex
                    ),
                    owner_id=user_id,
                    academic_year=assignment_year,
                    class_id=class_id,
                    subject_ref=(
                        None
                        if is_homeroom
                        else subject_ref
                    ),
                    component_ref=(
                        None
                        if is_homeroom
                        else component_ref
                    ),
                    role=role,
                    effective_from=effective_from,
                    effective_to=effective_to,
                    status=(
                        TeachingAssignmentStatus.ACTIVE
                    ),
                )
            )

            st.success(
                "\u0110\u00e3 th\u00eam "
                "ph\u00e2n c\u00f4ng."
            )

            st.rerun()

        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 th\u00eam "
                f"ph\u00e2n c\u00f4ng: {error}"
            )

    try:
        assignments = (
            assignment_repository.list_assignments(
                owner_id=user_id,
                academic_year=assignment_year,
            )
        )
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            f"ph\u00e2n c\u00f4ng: {error}"
        )
        return

    if not assignments:
        st.info(
            "Ch\u01b0a c\u00f3 ph\u00e2n c\u00f4ng "
            "cho n\u0103m h\u1ecdc n\u00e0y."
        )
        return

    migration_service = (
        TeachingAssignmentLegacyMigrationService()
    )

    legacy_previews = tuple(
        (
            item,
            migration_service.preview(item),
        )
        for item in assignments
        if migration_service.preview(item).is_legacy
    )

    if legacy_previews:
        st.warning(
            "Ph\\u00e1t hi\\u1ec7n ph\\u00e2n c\\u00f4ng c\\u0169 "
            "ch\\u01b0a theo c\\u1ea5u tr\\u00fac chu\\u1ea9n."
        )

        with st.expander(
            "Ph\\u00e2n c\\u00f4ng c\\u0169 c\\u1ea7n chu\\u1ea9n h\\u00f3a",
            expanded=True,
        ):
            st.info(
                "H\\u00e3y t\\u1ea1o l\\u1ea1i c\\u00e1c ph\\u00e2n c\\u00f4ng "
                "\\u0111\\u00fang b\\u1eb1ng bi\\u1ec3u m\\u1eabu Th\\u00eam "
                "ph\\u00e2n c\\u00f4ng \\u1edf ph\\u00eda tr\\u00ean. "
                "M\\u1ed7i d\\u00f2ng = 1 l\\u1edbp + 1 m\\u00f4n "
                "+ 0/1 ph\\u00e2n m\\u00f4n."
            )

            for item, preview in legacy_previews:
                st.markdown(
                    f"**ID:** `{item.assignment_id}`"
                )

                st.write(
                    {
                        "L\\u1edbp c\\u0169":
                            list(preview.class_refs),
                        "M\\u00f4n c\\u0169":
                            list(preview.subject_refs),
                        "Ph\\u00e2n m\\u00f4n c\\u0169":
                            list(preview.component_refs),
                        "T\\u1ef1 \\u0111\\u1ed9ng chu\\u1ea9n h\\u00f3a":
                            preview.can_auto_migrate,
                        "L\\u00fd do":
                            preview.reason,
                    }
                )

                if not preview.can_auto_migrate:
                    st.caption(
                        "B\\u1ea3n ghi n\\u00e0y c\\u00f3 nhi\\u1ec1u "
                        "chi\\u1ec1u d\\u1eef li\\u1ec7u; h\\u1ec7 th\\u1ed1ng "
                        "kh\\u00f4ng t\\u1ef1 suy \\u0111o\\u00e1n quan h\\u1ec7 "
                        "L\\u1edbp - M\\u00f4n - Ph\\u00e2n m\\u00f4n."
                    )

                st.divider()

    st.markdown(
        "#### Danh s\u00e1ch ph\u00e2n c\u00f4ng"
    )

    st.dataframe(
        [
            {
                "L\u1edbp": item.class_id,
                "M\u00f4n": (
                    item.subject_ref or ""
                ),
                "Ph\u00e2n m\u00f4n": (
                    item.component_ref or ""
                ),
                "Vai tr\u00f2": (
                    "Ch\u1ee7 nhi\u1ec7m"
                    if item.role
                    is TeachingAssignmentRole.HOMEROOM
                    else "Gi\u1ea3ng d\u1ea1y"
                ),
                "T\u1eeb ng\u00e0y": (
                    item.effective_from.isoformat()
                ),
                "\u0110\u1ebfn ng\u00e0y": (
                    item.effective_to.isoformat()
                ),
                "Tr\u1ea1ng th\u00e1i": (
                    item.status.value
                ),
            }
            for item in assignments
        ],
        use_container_width=True,
        hide_index=True,
    )

    for item in assignments:
        with st.container(
            border=True
        ):
            role_text = (
                "Ch\u1ee7 nhi\u1ec7m"
                if item.role
                is TeachingAssignmentRole.HOMEROOM
                else "Gi\u1ea3ng d\u1ea1y"
            )

            st.write(
                " | ".join(
                    part
                    for part in (
                        item.class_id,
                        item.subject_ref,
                        item.component_ref,
                        role_text,
                    )
                    if part
                )
            )

            actions = st.columns(2)

            with actions[0]:
                if (
                    item.status
                    is TeachingAssignmentStatus.ACTIVE
                ):
                    if st.button(
                        "Ng\u1eebng hi\u1ec7u l\u1ef1c",
                        key=(
                            "assignment_deactivate_"
                            + item.assignment_id
                        ),
                        use_container_width=True,
                    ):
                        assignment_repository.save(
                            assignment=replace(
                                item,
                                status=(
                                    TeachingAssignmentStatus.INACTIVE
                                ),
                            )
                        )
                        st.rerun()
                else:
                    if st.button(
                        "K\u00edch ho\u1ea1t l\u1ea1i",
                        key=(
                            "assignment_activate_"
                            + item.assignment_id
                        ),
                        use_container_width=True,
                    ):
                        assignment_repository.save(
                            assignment=replace(
                                item,
                                status=(
                                    TeachingAssignmentStatus.ACTIVE
                                ),
                            )
                        )
                        st.rerun()

            with actions[1]:
                if st.button(
                    "X\u00f3a",
                    key=(
                        "assignment_delete_"
                        + item.assignment_id
                    ),
                    use_container_width=True,
                ):
                    assignment_repository.delete(
                        assignment_id=(
                            item.assignment_id
                        )
                    )
                    st.rerun()

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


    elif selected == "Th\u1eddi kh\u00f3a bi\u1ec3u":
        from portal_v2.ui.teacher_timetable_streamlit import (
            render_teacher_timetable,
        )

        render_teacher_timetable(
            st=st,
            client=client,
            user_id=str(user_id),
        )

    elif selected == "\u0110\u0103ng k\u00fd m\u00f4n/ph\u00e2n m\u00f4n":
        from portal_v2.ui.teacher_subject_registration_streamlit import (
            render_teacher_subject_registration,
        )

        profile_repository = (
            SupabaseTeacherProfileRepository(
                client,
                str(user_id),
            )
        )

        try:
            profile = (
                profile_repository.get()
            )
        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
                f"h\u1ed3 s\u01a1 gi\u00e1o vi\u00ean: {error}"
            )
            return

        if profile is None:
            st.warning(
                "H\u00e3y khai b\u00e1o H\u1ed3 s\u01a1 "
                "gi\u00e1o vi\u00ean tr\u01b0\u1edbc."
            )
            return

        render_teacher_subject_registration(
            st=st,
            client=client,
            user_id=str(user_id),
            academic_year=(
                profile.default_academic_year
            ),
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

