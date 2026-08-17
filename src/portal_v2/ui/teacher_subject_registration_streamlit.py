from __future__ import annotations

from typing import Any
from uuid import uuid4

from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.adapters.supabase_teacher_subject_registration_repository import (
    SupabaseTeacherSubjectRegistrationRepository,
)
from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    SubjectComponentPolicy,
)
from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)
from educational_planning_v2.services.teacher_subject_registration_service import (
    TeacherSubjectRegistrationService,
)


def render_teacher_subject_registration(
    *,
    st,
    client: Any,
    user_id: str,
    academic_year: str,
) -> None:
    st.title(
        "\u0110\u0103ng k\u00fd m\u00f4n v\u00e0 ph\u00e2n m\u00f4n"
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

    # --------------------------------------------------------
    # LOAD ACTIVE CANONICAL SUBJECTS
    # --------------------------------------------------------

    try:
        subjects = (
            catalog_repository.list_subjects(
                status=CatalogStatus.ACTIVE,
            )
        )
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "danh m\u1ee5c m\u00f4n h\u1ecdc: "
            f"{error}"
        )
        return

    if not subjects:
        st.warning(
            "ADMIN ch\u01b0a thi\u1ebft l\u1eadp "
            "danh m\u1ee5c m\u00f4n h\u1ecdc ACTIVE."
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
            "\u0111\u0103ng k\u00fd m\u00f4n h\u1ecdc: "
            f"{error}"
        )
        return

    st.subheader(
        f"N\u0103m h\u1ecdc: {academic_year}"
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
        "Ph\u00e2n m\u00f4n",
        options=component_options,
        format_func=lambda value: (
            "\u2014 Kh\u00f4ng ch\u1ecdn ph\u00e2n m\u00f4n \u2014"
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
            "M\u00f4n n\u00e0y kh\u00f4ng s\u1eed d\u1ee5ng "
            "ph\u00e2n m\u00f4n. \u0110\u0103ng k\u00fd "
            "s\u1ebd \u0111\u01b0\u1ee3c l\u01b0u \u1edf c\u1ea5p m\u00f4n."
        )

    elif (
        selected_subject.component_policy
        is SubjectComponentPolicy.REQUIRED
    ):
        st.info(
            "M\u00f4n n\u00e0y b\u1eaft bu\u1ed9c "
            "ph\u1ea3i ch\u1ecdn ph\u00e2n m\u00f4n."
        )

    else:
        st.info(
            "C\u00f3 th\u1ec3 \u0111\u0103ng k\u00fd "
            "\u1edf c\u1ea5p m\u00f4n ho\u1eb7c "
            "ch\u1ecdn m\u1ed9t ph\u00e2n m\u00f4n c\u1ee5 th\u1ec3."
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

    required_component_missing = (
        selected_subject.component_policy
        is SubjectComponentPolicy.REQUIRED
        and not selected_component_id
    )

    if st.button(
        "\u0110\u0103ng k\u00fd m\u00f4n / ph\u00e2n m\u00f4n",
        type="primary",
        use_container_width=True,
        disabled=(
            already_registered
            or required_component_missing
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
