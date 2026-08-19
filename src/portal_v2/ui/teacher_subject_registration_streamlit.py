from __future__ import annotations

from typing import Any
from uuid import uuid4

from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.adapters.supabase_teacher_subject_assignment_repository import (
    SupabaseTeacherSubjectAssignmentRepository,
)
from educational_planning_v2.adapters.supabase_teacher_subject_registration_repository import (
    SupabaseTeacherSubjectRegistrationRepository,
)
from educational_planning_v2.adapters.supabase_teaching_assignment_repository import (
    SupabaseTeachingAssignmentRepository,
)
from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    SubjectComponentPolicy,
)
from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)
from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignmentStatus,
)
from educational_planning_v2.services.teacher_subject_registration_service import (
    TeacherSubjectRegistrationService,
)
from educational_planning_v2.services.teacher_subject_registration_lifecycle_service import (
    TeacherSubjectRegistrationLifecycleService,
)
from portal_v2.runtime.teacher_subject_assignment_consistency_runtime import (
    TeacherSubjectAssignmentConsistencyRuntime,
)


def render_teacher_subject_registration(
    *,
    st,
    client: Any,
    user_id: str,
    academic_year: str,
) -> None:
    st.title(
        "M\u00f4n \u0111\u01b0\u1ee3c ph\u00e2n c\u00f4ng v\u00e0 \u0111\u0103ng k\u00fd ph\u00e2n m\u00f4n"
    )

    st.caption(
        "Danh m\u1ee5c m\u00f4n v\u00e0 ph\u00e2n m\u00f4n "
        "\u0111\u01b0\u1ee3c ADMIN qu\u1ea3n l\u00fd th\u1ed1ng nh\u1ea5t. "
        "Gi\u00e1o vi\u00ean ch\u1ec9 \u0111\u0103ng k\u00fd "
        "trong danh m\u1ee5c \u0111ang ho\u1ea1t \u0111\u1ed9ng."
    )

    catalog_repository = (
        SupabaseSubjectCatalogRepository(
            client=client,
        )
    )

    subject_assignment_repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=client,
        )
    )

    registration_repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            client,
            user_id,
        )
    )

    validation_service = (
        TeacherSubjectRegistrationService(
            catalog_repository=(
                catalog_repository
            )
        )
    )

    assignment_repository = (
        SupabaseTeachingAssignmentRepository(
            client=client,
            user_id=user_id,
        )
    )

    lifecycle_service = (
        TeacherSubjectRegistrationLifecycleService(
            registration_repository=(
                registration_repository
            ),
            assignment_repository=(
                assignment_repository
            ),
        )
    )

    consistency_runtime = (
        TeacherSubjectAssignmentConsistencyRuntime(
            client=client,
            user_id=user_id,
        )
    )

    # --------------------------------------------------------
    # LOAD ADMIN-ASSIGNED SUBJECT SCOPE
    # --------------------------------------------------------

    try:
        subject_assignments = (
            subject_assignment_repository.list_assignments(
                teacher_id=user_id,
                academic_year=academic_year,
                status=(
                    TeacherSubjectAssignmentStatus.ACTIVE
                ),
            )
        )
    except Exception as error:
        st.error(
            "\u004b\u0068\u00f4\u006e\u0067 "
            "\u0074\u0068\u1ec3 "
            "\u0111\u1ecdc "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067 "
            "\u004d\u00f4\u006e "
            "\u0063\u1ee7\u0061 "
            "\u0041\u0044\u004d\u0049\u004e: "
            f"{error}"
        )
        return

    if not subject_assignments:
        st.warning(
            "\u0041\u0044\u004d\u0049\u004e "
            "\u0063\u0068\u01b0\u0061 "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067 "
            "\u004d\u00f4\u006e "
            "\u0063\u0068\u006f "
            "\u0062\u1ea1\u006e "
            "\u0074\u0072\u006f\u006e\u0067 "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc "
            "\u006e\u00e0\u0079."
        )
        return

    assigned_subject_ids = {
        item.subject_id
        for item in subject_assignments
    }

    try:
        active_catalog_subjects = (
            catalog_repository.list_subjects(
                status=CatalogStatus.ACTIVE,
            )
        )
    except Exception as error:
        st.error(
            "\u004b\u0068\u00f4\u006e\u0067 "
            "\u0074\u0068\u1ec3 "
            "\u0111\u1ecdc "
            "\u0064\u0061\u006e\u0068 "
            "\u006d\u1ee5\u0063 "
            "\u004d\u00f4\u006e: "
            f"{error}"
        )
        return

    subjects = tuple(
        subject
        for subject in active_catalog_subjects
        if (
            subject.subject_id
            in assigned_subject_ids
        )
    )

    if not subjects:
        st.error(
            "\u0043\u00f3 "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067 "
            "\u004d\u00f4\u006e "
            "\u006e\u0068\u01b0\u006e\u0067 "
            "\u006b\u0068\u00f4\u006e\u0067 "
            "\u0074\u00ec\u006d "
            "\u0074\u0068\u1ea5\u0079 "
            "\u004d\u00f4\u006e "
            "\u0041\u0043\u0054\u0049\u0056\u0045 "
            "\u0074\u01b0\u01a1\u006e\u0067 "
            "\u1ee9\u006e\u0067 "
            "\u0074\u0072\u006f\u006e\u0067 "
            "\u0053\u0075\u0062\u006a\u0065\u0063\u0074 "
            "\u0043\u0061\u0074\u0061\u006c\u006f\u0067."
        )
        return

    subject_by_id = {
        item.subject_id: item
        for item in subjects
    }

    # --------------------------------------------------------
    # LOAD CURRENT ACTIVE REGISTRATIONS
    # --------------------------------------------------------

    try:
        registrations = (
            registration_repository.list_registrations(
                owner_id=user_id,
                academic_year=academic_year,
                status=(
                    TeacherSubjectRegistrationStatus.ACTIVE
                ),
            )
        )
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "\u0111\u0103ng k\u00fd ph\u00e2n m\u00f4n: "
            f"{error}"
        )
        return

    registrations = tuple(
        registration
        for registration in registrations
        if (
            registration.subject_id
            in assigned_subject_ids
            and registration.component_id
            is not None
        )
    )

    st.subheader(
        f"N\u0103m h\u1ecdc: {academic_year}"
    )

    try:
        consistency_result = (
            consistency_runtime.audit(
                academic_year=academic_year,
            )
        )
    except Exception as error:
        st.warning(
            "\u004b\u0068\u00f4\u006e\u0067 "
            "\u0074\u0068\u1ec3 "
            "\u006b\u0069\u1ec3\u006d "
            "\u0074\u0072\u0061 "
            "\u0074\u00ed\u006e\u0068 "
            "\u006e\u0068\u1ea5\u0074 "
            "\u0071\u0075\u00e1\u006e "
            "\u0067\u0069\u1eef\u0061 "
            "\u0111\u0103\u006e\u0067 "
            "\u006b\u00fd "
            "\u0076\u00e0 "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067: "
            f"{error}"
        )
    else:
        if consistency_result.is_consistent:
            st.success(
                "\u0110\u0103\u006e\u0067 "
                "\u006b\u00fd "
                "\u006d\u00f4\u006e/"
                "\u0070\u0068\u00e2\u006e "
                "\u006d\u00f4\u006e "
                "\u0076\u00e0 "
                "\u0070\u0068\u00e2\u006e "
                "\u0063\u00f4\u006e\u0067 "
                "\u0067\u0069\u1ea3\u006e\u0067 "
                "\u0064\u1ea1\u0079 "
                "\u0111\u0061\u006e\u0067 "
                "\u006e\u0068\u1ea5\u0074 "
                "\u0071\u0075\u00e1\u006e."
            )
        else:
            st.error(
                "\u0050\u0068\u00e1\u0074 "
                "\u0068\u0069\u1ec7\u006e "
                "\u0064\u1eef "
                "\u006c\u0069\u1ec7\u0075 "
                "\u006d\u00e2\u0075 "
                "\u0074\u0068\u0075\u1eab\u006e: "
                "\u0063\u00f3 "
                "\u0070\u0068\u00e2\u006e "
                "\u0063\u00f4\u006e\u0067 "
                "\u0067\u0069\u1ea3\u006e\u0067 "
                "\u0064\u1ea1\u0079 "
                "\u0111\u0061\u006e\u0067 "
                "\u0068\u006f\u1ea1\u0074 "
                "\u0111\u1ed9\u006e\u0067 "
                "\u006e\u0068\u01b0\u006e\u0067 "
                "\u006b\u0068\u00f4\u006e\u0067 "
                "\u0063\u00f3 "
                "\u0111\u0103\u006e\u0067 "
                "\u006b\u00fd "
                "\u006d\u00f4\u006e/"
                "\u0070\u0068\u00e2\u006e "
                "\u006d\u00f4\u006e "
                "\u0041\u0043\u0054\u0049\u0056\u0045 "
                "\u0074\u01b0\u01a1\u006e\u0067 "
                "\u1ee9\u006e\u0067."
            )

            issue_rows = []

            for issue in consistency_result.issues:
                assignment = issue.assignment

                issue_rows.append(
                    {
                        "\u004c\u1edb\u0070": (
                            assignment.class_id
                        ),
                        "\u004d\u00f4\u006e": (
                            assignment.subject_ref
                            or "\u2014"
                        ),
                        "\u0050\u0068\u00e2\u006e "
                        "\u006d\u00f4\u006e": (
                            assignment.component_ref
                            or "\u2014"
                        ),
                        "\u004d\u00e3 "
                        "\u0070\u0068\u00e2\u006e "
                        "\u0063\u00f4\u006e\u0067": (
                            assignment.assignment_id
                        ),
                    }
                )

            st.dataframe(
                issue_rows,
                use_container_width=True,
                hide_index=True,
            )

            st.info(
                "\u0048\u00e3\u0079 "
                "\u0078\u1eed "
                "\u006c\u00fd "
                "\u0063\u00e1\u0063 "
                "\u0070\u0068\u00e2\u006e "
                "\u0063\u00f4\u006e\u0067 "
                "\u006d\u00e2\u0075 "
                "\u0074\u0068\u0075\u1eab\u006e "
                "\u0074\u0072\u01b0\u1edb\u0063 "
                "\u006b\u0068\u0069 "
                "\u0074\u0069\u1ebf\u0070 "
                "\u0074\u1ee5\u0063 "
                "\u0073\u1eed "
                "\u0064\u1ee5\u006e\u0067 "
                "\u0063\u00e1\u0063 "
                "\u0063\u0068\u1ee9\u0063 "
                "\u006e\u0103\u006e\u0067 "
                "\u006c\u1ead\u0070 "
                "\u006b\u1ebf "
                "\u0068\u006f\u1ea1\u0063\u0068."
            )

    subject_options = [
        item.subject_id
        for item in subjects
    ]

    selected_subject_id = st.selectbox(
        "M\u00f4n h\u1ecdc",
        options=subject_options,
        format_func=lambda value: (
            subject_by_id[value].name
        ),
        key=(
            "teacher_subject_registration_subject"
        ),
    )

    selected_subject = (
        subject_by_id[
            selected_subject_id
        ]
    )

    # --------------------------------------------------------
    # LOAD ACTIVE COMPONENTS FOR SELECTED SUBJECT
    # --------------------------------------------------------

    try:
        components = (
            catalog_repository.list_components(
                subject_id=selected_subject_id,
                status=CatalogStatus.ACTIVE,
            )
        )
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "danh m\u1ee5c ph\u00e2n m\u00f4n: "
            f"{error}"
        )
        return

    component_by_id = {
        item.component_id: item
        for item in components
    }

    component_options = (
        [""]
        + [
            item.component_id
            for item in components
        ]
    )

    component_disabled = (
        selected_subject.component_policy
        is SubjectComponentPolicy.NONE
    )

    selected_component_id = st.selectbox(
        "\u0050\u0068\u00e2\u006e "
        "\u006d\u00f4\u006e",
        options=component_options,
        format_func=lambda value: (
            "\u2014 "
            "\u0043\u0068\u1ecdn "
            "\u0070\u0068\u00e2\u006e "
            "\u006d\u00f4\u006e "
            "\u2014"
            if not value
            else component_by_id[value].name
        ),
        key=(
            "teacher_subject_registration_component_"
            + selected_subject_id
        ),
        disabled=component_disabled,
    )

    if (
        selected_subject.component_policy
        is SubjectComponentPolicy.NONE
    ):
        selected_component_id = ""

        st.info(
            "\u004d\u00f4\u006e "
            "\u006e\u00e0\u0079 "
            "\u006b\u0068\u00f4\u006e\u0067 "
            "\u0063\u00f3 "
            "\u0070\u0068\u00e2\u006e "
            "\u006d\u00f4\u006e. "
            "\u0042\u1ea1\u006e "
            "\u0111\u00e3 "
            "\u0111\u01b0\u1ee3\u0063 "
            "\u0041\u0044\u004d\u0049\u004e "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067 "
            "\u004d\u00f4\u006e "
            "\u006e\u00e0\u0079 "
            "\u0076\u00e0 "
            "\u006b\u0068\u00f4\u006e\u0067 "
            "\u0063\u1ea7\u006e "
            "\u0111\u0103\u006e\u0067 "
            "\u006b\u00fd "
            "\u0074\u0068\u00ea\u006d."
        )

    elif not components:
        st.warning(
            "\u004d\u00f4\u006e "
            "\u006e\u00e0\u0079 "
            "\u0063\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u0050\u0068\u00e2\u006e "
            "\u006d\u00f4\u006e "
            "\u0041\u0043\u0054\u0049\u0056\u0045."
        )

    else:
        st.info(
            "\u0043\u0068\u1ec9 "
            "\u0111\u0103\u006e\u0067 "
            "\u006b\u00fd "
            "\u0050\u0068\u00e2\u006e "
            "\u006d\u00f4\u006e "
            "\u0074\u0068\u0075\u1ed9\u0063 "
            "\u004d\u00f4\u006e "
            "\u0111\u00e3 "
            "\u0111\u01b0\u1ee3\u0063 "
            "\u0041\u0044\u004d\u0049\u004e "
            "\u0070\u0068\u00e2\u006e "
            "\u0063\u00f4\u006e\u0067."
        )

    # --------------------------------------------------------
    # PREVIEW
    # --------------------------------------------------------

    st.markdown(
        "#### \u0110\u0103ng k\u00fd s\u1ebd \u0111\u01b0\u1ee3c t\u1ea1o"
    )

    preview = st.columns(
        [1, 1]
    )

    preview[0].metric(
        "M\u00f4n",
        selected_subject.name,
    )

    preview[1].metric(
        "Ph\u00e2n m\u00f4n",
        (
            component_by_id[
                selected_component_id
            ].name
            if selected_component_id
            else "\u2014"
        ),
    )

    already_registered = any(
        (
            item.subject_id
            == selected_subject_id
            and (
                item.component_id or ""
            )
            == (
                selected_component_id or ""
            )
        )
        for item in registrations
    )

    if already_registered:
        st.info(
            "M\u00f4n/ph\u00e2n m\u00f4n n\u00e0y "
            "\u0111\u00e3 \u0111\u01b0\u1ee3c \u0111\u0103ng k\u00fd."
        )

    component_registration_unavailable = (
        selected_subject.component_policy
        is SubjectComponentPolicy.NONE
        or not selected_component_id
    )

    if st.button(
        "\u0110\u0103ng k\u00fd ph\u00e2n m\u00f4n",
        type="primary",
        use_container_width=True,
        disabled=(
            already_registered
            or component_registration_unavailable
        ),
    ):
        registration = (
            TeacherSubjectRegistration(
                registration_id=str(
                    uuid4()
                ),
                owner_id=user_id,
                academic_year=academic_year,
                subject_id=selected_subject_id,
                component_id=(
                    selected_component_id
                    or None
                ),
                status=(
                    TeacherSubjectRegistrationStatus.ACTIVE
                ),
            )
        )

        try:
            validation_service.validate_registration(
                registration=registration,
            )

            registration_repository.save(
                registration=registration,
            )
        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 l\u01b0u "
                f"\u0111\u0103ng k\u00fd: {error}"
            )
        else:
            st.success(
                "\u0110\u00e3 \u0111\u0103ng k\u00fd "
                "m\u00f4n/ph\u00e2n m\u00f4n."
            )
            st.rerun()

    # --------------------------------------------------------
    # CURRENT REGISTRATIONS
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "M\u00f4n v\u00e0 ph\u00e2n m\u00f4n "
        "\u0111\u00e3 \u0111\u0103ng k\u00fd"
    )

    if not registrations:
        st.info(
            "Ch\u01b0a c\u00f3 m\u00f4n ho\u1eb7c "
            "ph\u00e2n m\u00f4n \u0111\u01b0\u1ee3c "
            "\u0111\u0103ng k\u00fd trong n\u0103m h\u1ecdc n\u00e0y."
        )
        return

    component_cache = {}

    rows = []

    for registration in registrations:
        subject = subject_by_id.get(
            registration.subject_id
        )

        subject_name = (
            subject.name
            if subject is not None
            else registration.subject_id
        )

        component_name = "\u2014"

        if registration.component_id:
            if (
                registration.subject_id
                not in component_cache
            ):
                try:
                    component_cache[
                        registration.subject_id
                    ] = (
                        catalog_repository.list_components(
                            subject_id=(
                                registration.subject_id
                            )
                        )
                    )
                except Exception:
                    component_cache[
                        registration.subject_id
                    ] = ()

            matched = next(
                (
                    item
                    for item in component_cache[
                        registration.subject_id
                    ]
                    if (
                        item.component_id
                        == registration.component_id
                    )
                ),
                None,
            )

            component_name = (
                matched.name
                if matched is not None
                else registration.component_id
            )

        rows.append(
            {
                "M\u00f4n": subject_name,
                "Ph\u00e2n m\u00f4n": component_name,
                "Tr\u1ea1ng th\u00e1i": (
                    registration.status.value
                ),
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )


    st.markdown(
        "#### \u0051\u0075\u1ea3\u006e "
        "\u006c\u00fd "
        "\u0111\u0103\u006e\u0067 "
        "\u006b\u00fd"
    )

    st.caption(
        "\u0043\u0068\u1ec9 "
        "\u006e\u0067\u1eeb\u006e\u0067 "
        "\u0111\u0103\u006e\u0067 "
        "\u006b\u00fd "
        "\u006b\u0068\u0069 "
        "\u006d\u00f4\u006e/"
        "\u0070\u0068\u00e2\u006e "
        "\u006d\u00f4\u006e "
        "\u006b\u0068\u00f4\u006e\u0067 "
        "\u0063\u00f2\u006e "
        "\u0111\u01b0\u1ee3\u0063 "
        "\u0073\u1eed "
        "\u0064\u1ee5\u006e\u0067 "
        "\u0062\u1edf\u0069 "
        "\u0070\u0068\u00e2\u006e "
        "\u0063\u00f4\u006e\u0067 "
        "\u0067\u0069\u1ea3\u006e\u0067 "
        "\u0064\u1ea1\u0079 "
        "\u0111\u0061\u006e\u0067 "
        "\u0068\u006f\u1ea1\u0074 "
        "\u0111\u1ed9\u006e\u0067."
    )

    for registration in registrations:
        subject = subject_by_id.get(
            registration.subject_id
        )

        subject_name = (
            subject.name
            if subject is not None
            else registration.subject_id
        )

        component_name = "\u2014"

        if registration.component_id:
            if (
                registration.subject_id
                not in component_cache
            ):
                try:
                    component_cache[
                        registration.subject_id
                    ] = (
                        catalog_repository.list_components(
                            subject_id=(
                                registration.subject_id
                            )
                        )
                    )
                except Exception:
                    component_cache[
                        registration.subject_id
                    ] = ()

            matched = next(
                (
                    item
                    for item in component_cache[
                        registration.subject_id
                    ]
                    if (
                        item.component_id
                        == registration.component_id
                    )
                ),
                None,
            )

            component_name = (
                matched.name
                if matched is not None
                else registration.component_id
            )

        with st.container(
            border=True
        ):
            columns = st.columns(
                [3, 2, 1]
            )

            columns[0].write(
                f"**{subject_name}**"
            )

            columns[1].write(
                component_name
            )

            if columns[2].button(
                "\u004e\u0067\u1eeb\u006e\u0067 "
                "\u0111\u0103\u006e\u0067 "
                "\u006b\u00fd",
                key=(
                    "deactivate_subject_registration_"
                    + registration.registration_id
                ),
                use_container_width=True,
            ):
                try:
                    lifecycle_service.deactivate(
                        registration_id=(
                            registration.registration_id
                        )
                    )

                except ValueError as error:
                    if (
                        "used by active teaching assignments"
                        in str(error)
                    ):
                        st.error(
                            "\u004b\u0068\u00f4\u006e\u0067 "
                            "\u0074\u0068\u1ec3 "
                            "\u006e\u0067\u1eeb\u006e\u0067 "
                            "\u0111\u0103\u006e\u0067 "
                            "\u006b\u00fd "
                            "\u0076\u00ec "
                            "\u006d\u00f4\u006e/"
                            "\u0070\u0068\u00e2\u006e "
                            "\u006d\u00f4\u006e "
                            "\u006e\u00e0\u0079 "
                            "\u0111\u0061\u006e\u0067 "
                            "\u0111\u01b0\u1ee3\u0063 "
                            "\u0073\u1eed "
                            "\u0064\u1ee5\u006e\u0067 "
                            "\u0074\u0072\u006f\u006e\u0067 "
                            "\u0070\u0068\u00e2\u006e "
                            "\u0063\u00f4\u006e\u0067 "
                            "\u0067\u0069\u1ea3\u006e\u0067 "
                            "\u0064\u1ea1\u0079. "
                            "\u0048\u00e3\u0079 "
                            "\u006e\u0067\u1eeb\u006e\u0067 "
                            "\u0070\u0068\u00e2\u006e "
                            "\u0063\u00f4\u006e\u0067 "
                            "\u006c\u0069\u00ea\u006e "
                            "\u0071\u0075\u0061\u006e "
                            "\u0074\u0072\u01b0\u1edb\u0063."
                        )
                    else:
                        st.error(
                            "\u004b\u0068\u00f4\u006e\u0067 "
                            "\u0074\u0068\u1ec3 "
                            "\u006e\u0067\u1eeb\u006e\u0067 "
                            "\u0111\u0103\u006e\u0067 "
                            "\u006b\u00fd: "
                            f"{error}"
                        )

                except Exception as error:
                    st.error(
                        "\u004b\u0068\u00f4\u006e\u0067 "
                        "\u0074\u0068\u1ec3 "
                        "\u006e\u0067\u1eeb\u006e\u0067 "
                        "\u0111\u0103\u006e\u0067 "
                        "\u006b\u00fd: "
                        f"{error}"
                    )

                else:
                    st.success(
                        "\u0110\u00e3 "
                        "\u006e\u0067\u1eeb\u006e\u0067 "
                        "\u0111\u0103\u006e\u0067 "
                        "\u006b\u00fd "
                        "\u006d\u00f4\u006e/"
                        "\u0070\u0068\u00e2\u006e "
                        "\u006d\u00f4\u006e."
                    )
                    st.rerun()
