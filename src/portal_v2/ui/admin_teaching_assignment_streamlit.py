from __future__ import annotations

from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
    SupabaseAcademicYearConfigurationRepository,
)
from educational_planning_v2.adapters.supabase_admin_teacher_directory_repository import (
    SupabaseAdminTeacherDirectoryRepository,
)
from educational_planning_v2.adapters.supabase_admin_teaching_assignment_repository import (
    SupabaseAdminTeachingAssignmentRepository,
)
from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.adapters.supabase_teacher_subject_assignment_repository import (
    SupabaseTeacherSubjectAssignmentRepository,
)
from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignmentStatus,
)


def _teacher_label(
    teacher,
) -> str:
    parts = []

    if teacher.full_name:
        parts.append(
            teacher.full_name
        )

    if teacher.teacher_code:
        parts.append(
            f"[{teacher.teacher_code}]"
        )

    if teacher.school_name:
        parts.append(
            f"- {teacher.school_name}"
        )

    if parts:
        return " ".join(parts)

    return teacher.user_id


def render_admin_teaching_assignments(
    st,
    *,
    client=None,
) -> None:
    st.title(
        "Phân công giảng dạy"
    )

    st.caption(
        "ADMIN quản lý phân công giảng dạy "
        "và chủ nhiệm của giáo viên."
    )

    if client is None:
        st.error(
            "Supabase client chưa sẵn sàng."
        )
        return

    academic_year_repository = (
        SupabaseAcademicYearConfigurationRepository(
            client=client,
        )
    )

    teacher_repository = (
        SupabaseAdminTeacherDirectoryRepository(
            client=client,
        )
    )

    teacher_subject_repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=client,
        )
    )

    subject_repository = (
        SupabaseSubjectCatalogRepository(
            client=client,
        )
    )

    assignment_repository = (
        SupabaseAdminTeachingAssignmentRepository(
            client=client,
        )
    )

    try:
        current_year = (
            academic_year_repository.get_current()
        )
    except Exception as error:
        st.error(
            "Không thể đọc năm học hiện hành: "
            f"{error}"
        )
        return

    if current_year is None:
        st.warning(
            "Chưa có năm học hiện hành. "
            "Hãy cấu hình năm học trước."
        )
        return

    st.info(
        "Năm học hiện hành: "
        f"{current_year.academic_year}"
    )

    try:
        teachers = (
            teacher_repository.list_teachers()
        )
    except Exception as error:
        st.error(
            "Không thể đọc danh sách "
            f"giáo viên: {error}"
        )
        return

    if not teachers:
        st.warning(
            "Chưa có giáo viên trong "
            "danh mục."
        )
        return

    teacher_by_label = {
        _teacher_label(teacher): teacher
        for teacher in teachers
    }

    selected_teacher_label = (
        st.selectbox(
            "Giáo viên",
            options=tuple(
                teacher_by_label.keys()
            ),
        )
    )

    teacher = teacher_by_label[
        selected_teacher_label
    ]

    st.caption(
        f"Teacher ID: {teacher.user_id}"
    )

    try:
        subject_assignments = (
            teacher_subject_repository
            .list_assignments(
                teacher_id=teacher.user_id,
                academic_year=(
                    current_year.academic_year
                ),
                status=(
                    TeacherSubjectAssignmentStatus.ACTIVE
                ),
            )
        )
    except Exception as error:
        st.error(
            "Không thể đọc phân công môn: "
            f"{error}"
        )
        return

    subject_rows = []

    for subject_assignment in (
        subject_assignments
    ):
        try:
            subject = (
                subject_repository.get_subject(
                    subject_id=(
                        subject_assignment.subject_id
                    )
                )
            )
        except Exception:
            subject = None

        subject_rows.append(
            {
                "Môn": (
                    subject.name
                    if subject is not None
                    else (
                        subject_assignment.subject_id
                    )
                ),
                "Mã môn": (
                    subject_assignment.subject_id
                ),
                "Trạng thái": (
                    subject_assignment.status.value
                ),
            }
        )

    st.subheader(
        "Môn được phân công"
    )

    if subject_rows:
        st.dataframe(
            subject_rows,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Giáo viên chưa được ADMIN "
            "phân công môn trong năm học này."
        )

    try:
        assignments = (
            assignment_repository.list_assignments(
                owner_id=teacher.user_id,
                academic_year=(
                    current_year.academic_year
                ),
            )
        )
    except Exception as error:
        st.error(
            "Không thể đọc phân công "
            f"giảng dạy: {error}"
        )
        return

    st.subheader(
        "Phân công hiện có"
    )

    if not assignments:
        st.info(
            "Chưa có phân công giảng dạy "
            "hoặc chủ nhiệm."
        )
        return

    rows = []

    for assignment in assignments:
        subject_name = ""

        if assignment.subject_ref:
            try:
                subject = (
                    subject_repository.get_subject(
                        subject_id=(
                            assignment.subject_ref
                        )
                    )
                )
            except Exception:
                subject = None

            subject_name = (
                subject.name
                if subject is not None
                else assignment.subject_ref
            )

        component_name = ""

        if assignment.component_ref:
            try:
                component = (
                    subject_repository.get_component(
                        component_id=(
                            assignment.component_ref
                        )
                    )
                )
            except Exception:
                component = None

            component_name = (
                component.name
                if component is not None
                else assignment.component_ref
            )

        rows.append(
            {
                "Lớp": assignment.class_id,
                "Môn": subject_name,
                "Phân môn": component_name,
                "Vai trò": (
                    "Chủ nhiệm"
                    if assignment.role.value
                    == "HOMEROOM"
                    else "Giảng dạy"
                ),
                "Từ ngày": (
                    assignment.effective_from
                    .isoformat()
                ),
                "Đến ngày": (
                    assignment.effective_to
                    .isoformat()
                ),
                "Trạng thái": (
                    assignment.status.value
                ),
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )
