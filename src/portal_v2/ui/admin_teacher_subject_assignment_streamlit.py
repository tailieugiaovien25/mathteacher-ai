from __future__ import annotations

from uuid import uuid4

from educational_planning_v2.adapters.supabase_admin_teacher_directory_repository import (
    SupabaseAdminTeacherDirectoryRepository,
)
from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.adapters.supabase_teacher_subject_assignment_repository import (
    SupabaseTeacherSubjectAssignmentRepository,
)
from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
)
from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignment,
    TeacherSubjectAssignmentStatus,
)


def render_admin_teacher_subject_assignments(
    st,
    *,
    client=None,
) -> None:
    st.title(
        "\u0050\u0068\u00e2\u006e "
        "\u0063\u00f4\u006e\u0067 "
        "\u004d\u00f4\u006e"
    )

    st.caption(
        "\u0041\u0044\u004d\u0049\u004e "
        "\u0070\u0068\u00e2\u006e "
        "\u0063\u00f4\u006e\u0067 "
        "\u004d\u00f4\u006e "
        "\u0063\u0068\u006f "
        "\u0067\u0069\u00e1\u006f "
        "\u0076\u0069\u00ea\u006e "
        "\u0074\u0068\u0065\u006f "
        "\u006e\u0103\u006d "
        "\u0068\u1ecdc. "
        "\u0050\u0068\u00e2\u006e "
        "\u006d\u00f4\u006e "
        "\u006b\u0068\u00f4\u006e\u0067 "
        "\u0111\u01b0\u1ee3\u0063 "
        "\u0070\u0068\u00e2\u006e "
        "\u0063\u00f4\u006e\u0067 "
        "\u1edf "
        "\u0062\u01b0\u1edb\u0063 "
        "\u006e\u00e0\u0079."
    )

    if client is None:
        st.error(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u006b\u1ebf\u0074 "
            "\u006e\u1ed1\u0069 "
            "\u0064\u1eef "
            "\u006c\u0069\u1ec7\u0075 "
            "\u0041\u0044\u004d\u0049\u004e."
        )
        return

    teacher_repository = (
        SupabaseAdminTeacherDirectoryRepository(
            client=client,
        )
    )

    subject_repository = (
        SupabaseSubjectCatalogRepository(
            client=client,
        )
    )

    assignment_repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=client,
        )
    )

    try:
        teachers = (
            teacher_repository.list_teachers()
        )

        subjects = (
            subject_repository.list_subjects(
                status=CatalogStatus.ACTIVE,
            )
        )

    except Exception as error:
        st.error(
            "\u004b\u0068\u00f4\u006e\u0067 "
            "\u0074\u0068\u1ec3 "
            "\u0111\u1ecdc "
            "\u0064\u1eef "
            "\u006c\u0069\u1ec7\u0075 "
            "\u0067\u0069\u00e1\u006f "
            "\u0076\u0069\u00ea\u006e/"
            "\u006d\u00f4\u006e: "
            f"{error}"
        )
        return

    if not teachers:
        st.warning(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u0067\u0069\u00e1\u006f "
            "\u0076\u0069\u00ea\u006e "
            "\u0068\u1ee3\u0070 "
            "\u006c\u1ec7 "
            "\u0074\u0072\u006f\u006e\u0067 "
            "\u0064\u0061\u006e\u0068 "
            "\u006d\u1ee5\u0063."
        )
        return

    if not subjects:
        st.warning(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u004d\u00f4\u006e "
            "\u0041\u0043\u0054\u0049\u0056\u0045 "
            "\u0074\u0072\u006f\u006e\u0067 "
            "\u0053\u0075\u0062\u006a\u0065\u0063\u0074 "
            "\u0043\u0061\u0074\u0061\u006c\u006f\u0067."
        )
        return

    teacher_by_id = {
        teacher.user_id: teacher
        for teacher in teachers
    }

    subject_by_id = {
        subject.subject_id: subject
        for subject in subjects
    }

    st.subheader(
        "\u0054\u1ea1\u006f "
        "\u0070\u0068\u00e2\u006e "
        "\u0063\u00f4\u006e\u0067"
    )

    with st.form(
        "admin_teacher_subject_assignment_form"
    ):
        teacher_id = st.selectbox(
            "\u0047\u0069\u00e1\u006f "
            "\u0076\u0069\u00ea\u006e",
            options=tuple(
                teacher_by_id.keys()
            ),
            format_func=lambda value: (
                f"{teacher_by_id[value].full_name} "
                f"({teacher_by_id[value].teacher_code})"
            ),
        )

        academic_year = st.text_input(
            "\u004e\u0103\u006d "
            "\u0068\u1ecdc",
            placeholder="2026-2027",
        ).strip()

        subject_id = st.selectbox(
            "\u004d\u00f4\u006e",
            options=tuple(
                subject_by_id.keys()
            ),
            format_func=lambda value: (
                subject_by_id[value].name
            ),
        )

        st.info(
            "\u0041\u0044\u004d\u0049\u004e "
            "\u0063\u0068\u1ec9 "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067 "
            "\u1edf "
            "\u0063\u1ea5\u0070 "
            "\u004d\u00f4\u006e. "
            "\u0050\u0068\u00e2\u006e "
            "\u006d\u00f4\u006e "
            "\u0073\u1ebd "
            "\u0111\u01b0\u1ee3\u0063 "
            "\u0067\u0069\u00e1\u006f "
            "\u0076\u0069\u00ea\u006e "
            "\u0111\u0103\u006e\u0067 "
            "\u006b\u00fd "
            "\u0074\u0072\u006f\u006e\u0067 "
            "\u0070\u0068\u1ea1\u006d "
            "\u0076\u0069 "
            "\u004d\u00f4\u006e "
            "\u0111\u01b0\u1ee3\u0063 "
            "\u0067\u0069\u0061\u006f."
        )

        submitted = st.form_submit_button(
            "\u004c\u01b0\u0075 "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067",
            type="primary",
            width="stretch",
        )

    if submitted:
        try:
            if not academic_year:
                raise ValueError(
                    "\u004e\u0103\u006d "
                    "\u0068\u1ecdc "
                    "\u006b\u0068\u00f4\u006e\u0067 "
                    "\u0111\u01b0\u1ee3\u0063 "
                    "\u0111\u1ec3 "
                    "\u0074\u0072\u1ed1\u006e\u0067."
                )

            existing = (
                assignment_repository.find_subject_scope(
                    teacher_id=teacher_id,
                    academic_year=academic_year,
                    subject_id=subject_id,
                )
            )

            if existing:
                current = existing[0]

                if (
                    current.status
                    is TeacherSubjectAssignmentStatus.ACTIVE
                ):
                    st.warning(
                        "\u004d\u00f4\u006e "
                        "\u006e\u00e0\u0079 "
                        "\u0111\u00e3 "
                        "\u0111\u01b0\u1ee3\u0063 "
                        "\u0070\u0068\u00e2\u006e "
                        "\u0063\u00f4\u006e\u0067 "
                        "\u0063\u0068\u006f "
                        "\u0067\u0069\u00e1\u006f "
                        "\u0076\u0069\u00ea\u006e "
                        "\u0074\u0072\u006f\u006e\u0067 "
                        "\u006e\u0103\u006d "
                        "\u0068\u1ecdc "
                        "\u006e\u00e0\u0079."
                    )
                else:
                    assignment_repository.save(
                        assignment=(
                            TeacherSubjectAssignment(
                                assignment_id=(
                                    current.assignment_id
                                ),
                                teacher_id=(
                                    current.teacher_id
                                ),
                                academic_year=(
                                    current.academic_year
                                ),
                                subject_id=(
                                    current.subject_id
                                ),
                                status=(
                                    TeacherSubjectAssignmentStatus.ACTIVE
                                ),
                            )
                        )
                    )

                    st.success(
                        "\u0110\u00e3 "
                        "\u006b\u00ed\u0063\u0068 "
                        "\u0068\u006f\u1ea1\u0074 "
                        "\u006c\u1ea1\u0069 "
                        "\u0070\u0068\u00e2\u006e "
                        "\u0063\u00f4\u006e\u0067."
                    )

                    st.rerun()

            else:
                assignment_repository.save(
                    assignment=(
                        TeacherSubjectAssignment(
                            assignment_id=(
                                "tsa-"
                                + uuid4().hex
                            ),
                            teacher_id=teacher_id,
                            academic_year=academic_year,
                            subject_id=subject_id,
                            status=(
                                TeacherSubjectAssignmentStatus.ACTIVE
                            ),
                        )
                    )
                )

                st.success(
                    "\u0110\u00e3 "
                    "\u0074\u1ea1\u006f "
                    "\u0070\u0068\u00e2\u006e "
                    "\u0063\u00f4\u006e\u0067 "
                    "\u004d\u00f4\u006e "
                    "\u0074\u0068\u00e0\u006e\u0068 "
                    "\u0063\u00f4\u006e\u0067."
                )

                st.rerun()

        except Exception as error:
            st.error(
                "\u004b\u0068\u00f4\u006e\u0067 "
                "\u0074\u0068\u1ec3 "
                "\u006c\u01b0\u0075 "
                "\u0070\u0068\u00e2\u006e "
                "\u0063\u00f4\u006e\u0067: "
                f"{error}"
            )

    st.divider()

    st.subheader(
        "\u0044\u0061\u006e\u0068 "
        "\u0073\u00e1\u0063\u0068 "
        "\u0070\u0068\u00e2\u006e "
        "\u0063\u00f4\u006e\u0067"
    )

    try:
        assignments = (
            assignment_repository.list_assignments()
        )
    except Exception as error:
        st.error(
            "\u004b\u0068\u00f4\u006e\u0067 "
            "\u0074\u0068\u1ec3 "
            "\u0111\u1ecdc "
            "\u0064\u0061\u006e\u0068 "
            "\u0073\u00e1\u0063\u0068 "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067: "
            f"{error}"
        )
        return

    if not assignments:
        st.info(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067 "
            "\u004d\u00f4\u006e."
        )
        return

    rows = []

    for assignment in assignments:
        teacher = teacher_by_id.get(
            assignment.teacher_id
        )

        subject = subject_by_id.get(
            assignment.subject_id
        )

        rows.append(
            {
                "\u0047\u0069\u00e1\u006f "
                "\u0076\u0069\u00ea\u006e": (
                    teacher.full_name
                    if teacher is not None
                    else assignment.teacher_id
                ),
                "\u004d\u00e3 "
                "\u0047\u0056": (
                    teacher.teacher_code
                    if teacher is not None
                    else ""
                ),
                "\u004e\u0103\u006d "
                "\u0068\u1ecdc": (
                    assignment.academic_year
                ),
                "\u004d\u00f4\u006e": (
                    subject.name
                    if subject is not None
                    else assignment.subject_id
                ),
                "\u0054\u0072\u1ea1\u006e\u0067 "
                "\u0074\u0068\u00e1\u0069": (
                    assignment.status.value
                ),
            }
        )

    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
    )
