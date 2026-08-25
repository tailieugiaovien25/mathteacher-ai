from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
    SupabaseAcademicYearConfigurationRepository,
)
from educational_planning_v2.adapters.supabase_admin_teacher_directory_repository import (
    SupabaseAdminTeacherDirectoryRepository,
)
from educational_planning_v2.adapters.supabase_admin_teaching_assignment_repository import (
    SupabaseAdminTeachingAssignmentRepository,
)
from educational_planning_v2.adapters.supabase_assignment_round_repository import (
    SupabaseAssignmentRoundRepository,
)
from educational_planning_v2.adapters.supabase_class_catalog_repository import (
    SupabaseClassCatalogRepository,
)
from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.adapters.supabase_teacher_subject_assignment_repository import (
    SupabaseTeacherSubjectAssignmentRepository,
)
from educational_planning_v2.models.assignment_round import (
    AssignmentRound,
    AssignmentRoundStatus,
)
from educational_planning_v2.models.class_catalog import (
    ClassCatalogStatus,
)
from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
)
from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignment,
    TeacherSubjectAssignmentStatus,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)


def _teacher_label(
    teacher,
) -> str:
    label = teacher.full_name

    if teacher.teacher_code:
        label += (
            f" ({teacher.teacher_code})"
        )

    return label or teacher.user_id


def render_admin_assignment_workspace(
    st,
    *,
    client=None,
) -> None:
    if client is None:
        st.error(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u006b\u1ebf\u0074 "
            "\u006e\u1ed1\u0069 "
            "\u0053\u0075\u0070\u0061\u0062\u0061\u0073\u0065."
        )
        return

    year_repository = (
        SupabaseAcademicYearConfigurationRepository(
            client=client,
        )
    )

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

    subject_assignment_repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=client,
        )
    )

    teaching_repository = (
        SupabaseAdminTeachingAssignmentRepository(
            client=client,
        )
    )


    round_repository = (
        SupabaseAssignmentRoundRepository(
            client=client,
        )
    )

    class_repository = (
        SupabaseClassCatalogRepository(
            client=client,
        )
    )

    try:
        current_year = (
            year_repository.get_current()
        )

        teachers = (
            teacher_repository.list_teachers()
        )

        active_role_response = (
            client.table("portal_roles")
            .select("user_id,is_active")
            .eq("role", "teacher")
            .eq("is_active", True)
            .execute()
        )
        active_teacher_ids = {
            str(row.get("user_id", "") or "").strip()
            for row in (getattr(active_role_response, "data", ()) or ())
            if isinstance(row, dict)
        }
        teachers = tuple(
            teacher
            for teacher in teachers
            if teacher.user_id in active_teacher_ids
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
            "\u006c\u0069\u1ec7\u0075: "
            f"{error}"
        )
        return

    if current_year is None:
        st.warning(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc "
            "\u0068\u0069\u1ec7\u006e "
            "\u0068\u00e0\u006e\u0068."
        )
        return

    try:
        classes = class_repository.list_classes(
            academic_year=current_year.academic_year,
            status=ClassCatalogStatus.ACTIVE,
        )
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "danh s\u00e1ch l\u1edbp: "
            f"{error}"
        )
        return

    if not classes:
        st.warning(
            "Ch\u01b0a c\u00f3 l\u1edbp ACTIVE "
            "trong n\u0103m h\u1ecdc hi\u1ec7n h\u00e0nh."
        )
        return

    class_by_id = {
        item.class_id: item
        for item in classes
    }


    st.title(
        "B\u1ea3ng ph\u00e2n c\u00f4ng "
        "chuy\u00ean m\u00f4n "
        f"n\u0103m h\u1ecdc "
        f"{current_year.academic_year}"
    )

    st.caption(
        "ADMIN qu\u1ea3n l\u00fd t\u1eadp trung "
        "ph\u00e2n c\u00f4ng gi\u00e1o vi\u00ean, "
        "l\u1edbp d\u1ea1y, m\u00f4n d\u1ea1y, "
        "ph\u00e2n m\u00f4n v\u00e0 th\u1eddi gian "
        "c\u00f3 hi\u1ec7u l\u1ef1c."
    )

    try:
        assignment_rounds = (
            round_repository.list_rounds(
                academic_year=(
                    current_year.academic_year
                ),
            )
        )
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "c\u00e1c l\u1ea7n ph\u00e2n c\u00f4ng: "
            f"{error}"
        )
        return

    if not assignment_rounds:
        st.warning(
            "Ch\u01b0a c\u00f3 l\u1ea7n "
            "ph\u00e2n c\u00f4ng cho "
            "n\u0103m h\u1ecdc n\u00e0y."
        )

    round_by_id = {
        item.round_id: item
        for item in assignment_rounds
    }

    round_session_key = (
        "admin_assignment_round_id"
    )

    selected_round_id = (
        st.session_state.get(
            round_session_key
        )
    )

    if (
        selected_round_id
        not in round_by_id
    ):
        selected_round_id = (
            assignment_rounds[-1].round_id
            if assignment_rounds
            else None
        )

        st.session_state[
            round_session_key
        ] = selected_round_id

    round_columns = st.columns(
        max(
            1,
            len(assignment_rounds) + 1,
        )
    )

    for index, item in enumerate(
        assignment_rounds
    ):
        with round_columns[index]:
            selected = (
                item.round_id
                == selected_round_id
            )

            if st.button(
                item.label,
                key=(
                    "admin_assignment_round_"
                    + item.round_id
                ),
                type=(
                    "primary"
                    if selected
                    else "secondary"
                ),
                width="stretch",
            ):
                st.session_state[
                    round_session_key
                ] = item.round_id

                st.rerun()

    with round_columns[
        len(assignment_rounds)
    ]:
        if st.button(
            "+ Th\u00eam l\u1ea7n",
            key="admin_assignment_add_round",
            width="stretch",
        ):
            st.session_state[
                "admin_assignment_add_round_open"
            ] = True

    if st.session_state.get(
        "admin_assignment_add_round_open",
        False,
    ):
        next_round_number = (
            max(
                (
                    item.round_number
                    for item
                    in assignment_rounds
                ),
                default=0,
            )
            + 1
        )

        with st.form(
            "admin_assignment_add_round_form"
        ):
            st.markdown(
                f"**T\u1ea1o L\u1ea7n "
                f"{next_round_number}**"
            )

            round_effective_from = (
                st.date_input(
                    "T\u1eeb ng\u00e0y",
                    value=(
                        current_year.start_date
                    ),
                    min_value=(
                        current_year.start_date
                    ),
                    max_value=(
                        current_year.end_date
                    ),
                )
            )

            round_submit_columns = (
                st.columns(2)
            )

            with round_submit_columns[0]:
                create_round = (
                    st.form_submit_button(
                        "T\u1ea1o l\u1ea7n "
                        "ph\u00e2n c\u00f4ng",
                        type="primary",
                        width="stretch",
                    )
                )

            with round_submit_columns[1]:
                cancel_round = (
                    st.form_submit_button(
                        "H\u1ee7y",
                        width="stretch",
                    )
                )

        if cancel_round:
            st.session_state[
                "admin_assignment_add_round_open"
            ] = False
            st.rerun()

        if create_round:
            try:
                new_round = (
                    round_repository.save(
                        assignment_round=(
                            AssignmentRound(
                                round_id=(
                                    "round-"
                                    + uuid4().hex
                                ),
                                academic_year=(
                                    current_year
                                    .academic_year
                                ),
                                round_number=(
                                    next_round_number
                                ),
                                effective_from=(
                                    round_effective_from
                                ),
                                status=(
                                    AssignmentRoundStatus
                                    .ACTIVE
                                ),
                            )
                        )
                    )
                )
            except Exception as error:
                st.error(
                    "Kh\u00f4ng th\u1ec3 t\u1ea1o "
                    "l\u1ea7n ph\u00e2n c\u00f4ng: "
                    f"{error}"
                )
            else:
                st.session_state[
                    round_session_key
                ] = new_round.round_id

                st.session_state[
                    "admin_assignment_add_round_open"
                ] = False

                st.rerun()

    selected_round = (
        round_by_id.get(
            selected_round_id
        )
    )

    if selected_round is not None:
        st.caption(
            "L\u1ea7n \u0111ang ch\u1ecdn: "
            f"{selected_round.label} "
            "\u2022 T\u1eeb ng\u00e0y "
            f"{selected_round.effective_from.isoformat()}"
        )

    if not teachers:
        st.warning(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u0067\u0069\u00e1\u006f "
            "\u0076\u0069\u00ea\u006e."
        )
        return

    if not subjects:
        st.warning(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u006d\u00f4\u006e "
            "\u0041\u0043\u0054\u0049\u0056\u0045."
        )
        return

    st.info(
        "\u004e\u0103\u006d "
        "\u0068\u1ecdc "
        "\u0068\u0069\u1ec7\u006e "
        "\u0068\u00e0\u006e\u0068: "
        f"{current_year.academic_year}"
    )

    teacher_by_id = {
        teacher.user_id: teacher
        for teacher in teachers
    }

    target_teacher_id = st.session_state.pop(
        "admin_assignment_target_teacher_id",
        None,
    )

    if target_teacher_id in teacher_by_id:
        st.session_state[
            "admin_assignment_row_teacher"
        ] = target_teacher_id
    elif target_teacher_id:
        st.warning(
            "Giáo viên được chọn không còn hiệu lực hoặc không có hồ sơ hợp lệ."
        )

    subject_by_id = {
        subject.subject_id: subject
        for subject in subjects
    }

    st.subheader(
        "\u0054\u1ea1\u006f "
        "\u0070\u0068\u00e2\u006e "
        "\u0063\u00f4\u006e\u0067"
    )

    teacher_options = (
        (None,)
        + tuple(teacher_by_id.keys())
    )

    class_options = (
        (None,)
        + tuple(class_by_id.keys())
    )

    subject_options = (
        (None,)
        + tuple(subject_by_id.keys())
    )

    if selected_round is not None:
        first_valid_date = max(
            current_year.start_date,
            selected_round.effective_from,
        )
    else:
        first_valid_date = current_year.start_date

    date_options = (
        (None,)
        + tuple(
            first_valid_date
            + timedelta(days=offset)
            for offset in range(
                (
                    current_year.end_date
                    - first_valid_date
                ).days
                + 1
            )
        )
    )

    header_columns = st.columns(
        [2.4, 1.25, 1.5, 1.5, 1.45, 0.7]
    )

    header_columns[0].markdown(
        "**H\u1ecd v\u00e0 t\u00ean GV**"
    )
    header_columns[1].markdown(
        "**L\u1edbp d\u1ea1y**"
    )
    header_columns[2].markdown(
        "**M\u00f4n**"
    )
    header_columns[3].markdown(
        "**Ph\u00e2n m\u00f4n**"
    )
    header_columns[4].markdown(
        "**T\u1eeb ng\u00e0y**"
    )
    header_columns[5].markdown(
        "**Thao t\u00e1c**"
    )

    row_columns = st.columns(
        [2.4, 1.25, 1.5, 1.5, 1.45, 0.7]
    )

    with row_columns[0]:
        teacher_id = st.selectbox(
            "H\u1ecd v\u00e0 t\u00ean GV",
            options=teacher_options,
            format_func=lambda value: (
                "\u2014 Ch\u1ecdn GV \u2014"
                if value is None
                else _teacher_label(
                    teacher_by_id[value]
                )
            ),
            key="admin_assignment_row_teacher",
            label_visibility="collapsed",
        )

    with row_columns[1]:
        class_id = st.selectbox(
            "L\u1edbp d\u1ea1y",
            options=class_options,
            format_func=lambda value: (
                "\u2014 Ch\u1ecdn l\u1edbp \u2014"
                if value is None
                else class_by_id[value].display_name
            ),
            key="admin_assignment_row_class",
            label_visibility="collapsed",
        )

    with row_columns[2]:
        subject_id = st.selectbox(
            "M\u00f4n",
            options=subject_options,
            format_func=lambda value: (
                "\u2014 Ch\u1ecdn m\u00f4n \u2014"
                if value is None
                else subject_by_id[value].name
            ),
            key="admin_assignment_row_subject",
            label_visibility="collapsed",
        )

    components = ()

    if subject_id is not None:
        components = (
            subject_repository.list_components(
                subject_id=subject_id,
                status=CatalogStatus.ACTIVE,
            )
        )

    component_by_id = {
        item.component_id: item
        for item in components
    }

    component_options = (
        (None,)
        + tuple(component_by_id.keys())
    )

    with row_columns[3]:
        component_id = st.selectbox(
            "Ph\u00e2n m\u00f4n",
            options=component_options,
            format_func=lambda value: (
                "\u2014"
                if value is None
                else component_by_id[value].name
            ),
            key="admin_assignment_row_component",
            label_visibility="collapsed",
            disabled=(subject_id is None),
        )

    with row_columns[4]:
        effective_from = st.selectbox(
            "T\u1eeb ng\u00e0y",
            options=date_options,
            format_func=lambda value: (
                "\u2014 Ch\u1ecdn ng\u00e0y \u2014"
                if value is None
                else value.strftime("%d/%m/%Y")
            ),
            key="admin_assignment_row_date",
            label_visibility="collapsed",
        )

    with row_columns[5]:
        delete_row = st.button(
            "X\u00f3a",
            key="admin_assignment_row_delete",
            width="stretch",
        )

    if delete_row:
        for key in (
            "admin_assignment_row_teacher",
            "admin_assignment_row_class",
            "admin_assignment_row_subject",
            "admin_assignment_row_component",
            "admin_assignment_row_date",
        ):
            st.session_state.pop(key, None)

        st.rerun()

    st.write("")

    action_columns = st.columns(
        [5.0, 1.5]
    )

    with action_columns[1]:
        create_assignment = st.button(
            "+ T\u1ea1o ph\u00e2n c\u00f4ng",
            type="primary",
            width="stretch",
            key="admin_assignment_create",
        )

    if create_assignment:
        try:
            if selected_round is None:
                raise ValueError(
                    "Ch\u01b0a ch\u1ecdn "
                    "l\u1ea7n ph\u00e2n c\u00f4ng."
                )

            if teacher_id is None:
                raise ValueError(
                    "Ch\u01b0a ch\u1ecdn "
                    "gi\u00e1o vi\u00ean."
                )

            if class_id is None:
                raise ValueError(
                    "Ch\u01b0a ch\u1ecdn "
                    "l\u1edbp d\u1ea1y."
                )

            if subject_id is None:
                raise ValueError(
                    "Ch\u01b0a ch\u1ecdn m\u00f4n."
                )

            if effective_from is None:
                raise ValueError(
                    "Ch\u01b0a ch\u1ecdn "
                    "t\u1eeb ng\u00e0y."
                )

            existing_scope = (
                subject_assignment_repository
                .find_subject_scope(
                    teacher_id=teacher_id,
                    academic_year=(
                        current_year.academic_year
                    ),
                    subject_id=subject_id,
                )
            )

            if existing_scope:
                scope = existing_scope[0]

                if (
                    scope.status
                    is not
                    TeacherSubjectAssignmentStatus.ACTIVE
                ):
                    subject_assignment_repository.save(
                        assignment=(
                            TeacherSubjectAssignment(
                                assignment_id=(
                                    scope.assignment_id
                                ),
                                teacher_id=teacher_id,
                                academic_year=(
                                    current_year.academic_year
                                ),
                                subject_id=subject_id,
                                status=(
                                    TeacherSubjectAssignmentStatus.ACTIVE
                                ),
                            )
                        )
                    )
            else:
                subject_assignment_repository.save(
                    assignment=(
                        TeacherSubjectAssignment(
                            assignment_id=(
                                "tsa-" + uuid4().hex
                            ),
                            teacher_id=teacher_id,
                            academic_year=(
                                current_year.academic_year
                            ),
                            subject_id=subject_id,
                            status=(
                                TeacherSubjectAssignmentStatus.ACTIVE
                            ),
                        )
                    )
                )

            teaching_repository.save(
                assignment=TeachingAssignment(
                    assignment_id=(
                        "assign-" + uuid4().hex
                    ),
                    owner_id=teacher_id,
                    academic_year=(
                        current_year.academic_year
                    ),
                    class_id=class_id,
                    subject_ref=subject_id,
                    component_ref=component_id,
                    role=(
                        TeachingAssignmentRole.TEACHING
                    ),
                    effective_from=effective_from,
                    effective_to=(
                        current_year.end_date
                    ),
                    assignment_round_id=(
                        selected_round.round_id
                    ),
                    status=(
                        TeachingAssignmentStatus.ACTIVE
                    ),
                )
            )

        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 "
                "t\u1ea1o ph\u00e2n c\u00f4ng: "
                f"{error}"
            )

        else:
            for key in (
                "admin_assignment_row_teacher",
                "admin_assignment_row_class",
                "admin_assignment_row_subject",
                "admin_assignment_row_component",
                "admin_assignment_row_date",
            ):
                st.session_state.pop(key, None)

            st.success(
                "\u0110\u00e3 t\u1ea1o "
                "ph\u00e2n c\u00f4ng."
            )

            st.rerun()

    st.divider()

    st.subheader(
        "\u0044\u0061\u006e\u0068 "
        "\u0073\u00e1\u0063\u0068 "
        "\u0070\u0068\u00e2\u006e "
        "\u0063\u00f4\u006e\u0067"
    )

    assignments = (
        teaching_repository.list_assignments(
            academic_year=(
                current_year.academic_year
            ),
        )
    )

    if not assignments:
        st.info(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067."
        )
        return

    rows = []

    for assignment in assignments:
        teacher = teacher_by_id.get(
            assignment.owner_id
        )

        subject_name = ""

        if assignment.subject_ref:
            subject = subject_by_id.get(
                assignment.subject_ref
            )

            subject_name = (
                subject.name
                if subject is not None
                else assignment.subject_ref
            )

        component_name = ""

        if assignment.component_ref:
            component = (
                subject_repository.get_component(
                    component_id=(
                        assignment.component_ref
                    )
                )
            )

            component_name = (
                component.name
                if component is not None
                else assignment.component_ref
            )

        class_item = class_by_id.get(
            assignment.class_id
        )

        class_code = (
            class_item.class_code
            if class_item is not None
            else assignment.class_id
        )

        class_name = (
            class_item.class_name
            if class_item is not None
            else ""
        )

        rows.append(
            {
                "M\u00e3 l\u1edbp":
                    class_code,

                "Gi\u00e1o vi\u00ean": (
                    teacher.full_name
                    if teacher is not None
                    else assignment.owner_id
                ),

                "M\u00e3 GV": (
                    teacher.teacher_code
                    if teacher is not None
                    else ""
                ),

                "T\u00ean l\u1edbp":
                    class_name,

                "M\u00f4n":
                    subject_name,

                "Ph\u00e2n m\u00f4n":
                    component_name,

                "T\u1eeb ng\u00e0y":
                    assignment.effective_from.isoformat(),

                "\u0110\u1ebfn ng\u00e0y":
                    assignment.effective_to.isoformat(),
            }
        )


    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
    )


    st.divider()

    st.subheader(
        "\u0051\u0075\u1ea3\u006e "
        "\u006c\u00fd "
        "\u0070\u0068\u00e2\u006e "
        "\u0063\u00f4\u006e\u0067"
    )

    assignment_by_id = {
        assignment.assignment_id:
            assignment
        for assignment in assignments
    }

    selected_assignment_id = (
        st.selectbox(
            "\u0050\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067 "
            "\u0063\u1ea7\u006e "
            "\u0071\u0075\u1ea3\u006e "
            "\u006c\u00fd",
            options=tuple(
                assignment_by_id.keys()
            ),
            format_func=lambda value: (
                " | ".join(
                    part
                    for part in (
                        value,
                        assignment_by_id[
                            value
                        ].class_id,
                        (
                            subject_by_id.get(
                                assignment_by_id[
                                    value
                                ].subject_ref
                            ).name
                            if (
                                assignment_by_id[
                                    value
                                ].subject_ref
                                in subject_by_id
                            )
                            else (
                                assignment_by_id[
                                    value
                                ].subject_ref
                                or ""
                            )
                        ),
                        assignment_by_id[
                            value
                        ].status.value,
                    )
                    if part
                )
            ),
            key=(
                "admin_assignment_manage_id"
            ),
        )
    )

    selected_assignment = (
        assignment_by_id[
            selected_assignment_id
        ]
    )

    st.caption(
        f"Assignment ID: "
        f"{selected_assignment.assignment_id}"
    )

    action_columns = st.columns(
        2
    )

    with action_columns[0]:
        if (
            selected_assignment.status
            is TeachingAssignmentStatus.ACTIVE
        ):
            if st.button(
                "\u004e\u0067\u1eeb\u006e\u0067 "
                "\u0068\u0069\u1ec7\u0075 "
                "\u006c\u1ef1\u0063",
                width="stretch",
                key=(
                    "admin_assignment_deactivate"
                ),
            ):
                teaching_repository.save(
                    assignment=TeachingAssignment(
                        assignment_id=(
                            selected_assignment.assignment_id
                        ),
                        owner_id=(
                            selected_assignment.owner_id
                        ),
                        academic_year=(
                            selected_assignment.academic_year
                        ),
                        class_id=(
                            selected_assignment.class_id
                        ),
                        subject_ref=(
                            selected_assignment.subject_ref
                        ),
                        component_ref=(
                            selected_assignment.component_ref
                        ),
                        role=(
                            selected_assignment.role
                        ),
                        effective_from=(
                            selected_assignment.effective_from
                        ),
                        effective_to=(
                            selected_assignment.effective_to
                        ),
                        status=(
                            TeachingAssignmentStatus.INACTIVE
                        ),
                    )
                )

                st.success(
                    "\u0110\u00e3 "
                    "\u006e\u0067\u1eeb\u006e\u0067 "
                    "\u0068\u0069\u1ec7\u0075 "
                    "\u006c\u1ef1\u0063 "
                    "\u0070\u0068\u00e2\u006e "
                    "\u0063\u00f4\u006e\u0067."
                )

                st.rerun()

        else:
            if st.button(
                "\u004b\u00ed\u0063\u0068 "
                "\u0068\u006f\u1ea1\u0074 "
                "\u006c\u1ea1\u0069",
                width="stretch",
                key=(
                    "admin_assignment_activate"
                ),
            ):
                teaching_repository.save(
                    assignment=TeachingAssignment(
                        assignment_id=(
                            selected_assignment.assignment_id
                        ),
                        owner_id=(
                            selected_assignment.owner_id
                        ),
                        academic_year=(
                            selected_assignment.academic_year
                        ),
                        class_id=(
                            selected_assignment.class_id
                        ),
                        subject_ref=(
                            selected_assignment.subject_ref
                        ),
                        component_ref=(
                            selected_assignment.component_ref
                        ),
                        role=(
                            selected_assignment.role
                        ),
                        effective_from=(
                            selected_assignment.effective_from
                        ),
                        effective_to=(
                            selected_assignment.effective_to
                        ),
                        status=(
                            TeachingAssignmentStatus.ACTIVE
                        ),
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

    with action_columns[1]:
        confirm_delete = (
            st.checkbox(
                "\u0058\u00e1\u0063 "
                "\u006e\u0068\u1ead\u006e "
                "\u0078\u00f3\u0061 "
                "\u0070\u0068\u00e2\u006e "
                "\u0063\u00f4\u006e\u0067 "
                "\u006e\u00e0\u0079",
                key=(
                    "admin_assignment_confirm_delete"
                ),
            )
        )

        if st.button(
            "\u0058\u00f3\u0061",
            width="stretch",
            disabled=(
                not confirm_delete
            ),
            key=(
                "admin_assignment_delete"
            ),
        ):
            teaching_repository.delete(
                assignment_id=(
                    selected_assignment.assignment_id
                )
            )

            st.success(
                "\u0110\u00e3 "
                "\u0078\u00f3\u0061 "
                "\u0070\u0068\u00e2\u006e "
                "\u0063\u00f4\u006e\u0067."
            )

            st.rerun()
