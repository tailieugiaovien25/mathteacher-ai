from __future__ import annotations

from typing import Any
from uuid import uuid4

from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    Subject,
    SubjectComponent,
    SubjectComponentPolicy,
)


def _show_delete_success_dialog(
    st,
) -> None:
    if not st.session_state.get(
        "admin_subject_catalog_delete_success",
        False,
    ):
        return

    @st.dialog(
        "Th\u00f4ng b\u00e1o"
    )
    def dialog():
        st.success(
            "\u0110\u00e3 x\u00f3a th\u00e0nh c\u00f4ng"
        )

        if st.button(
            "\u0110\u00f3ng",
            type="primary",
            width="stretch",
            key="admin_subject_catalog_delete_dialog_close",
        ):
            st.session_state.pop(
                "admin_subject_catalog_delete_success",
                None,
            )
            st.rerun()

    dialog()


def render_admin_subject_catalog(
    st,
    *,
    client: Any,
) -> None:
    st.title(
        "M\u00f4n & Ph\u00e2n m\u00f4n"
    )

    st.caption(
        "ADMIN qu\u1ea3n l\u00fd danh m\u1ee5c "
        "m\u00f4n v\u00e0 ph\u00e2n m\u00f4n "
        "d\u00f9ng chung trong to\u00e0n h\u1ec7 th\u1ed1ng."
    )

    _show_delete_success_dialog(
        st,
    )

    if client is None:
        st.error(
            "Ch\u01b0a c\u00f3 k\u1ebft n\u1ed1i "
            "d\u1eef li\u1ec7u ADMIN."
        )
        return

    repository = (
        SupabaseSubjectCatalogRepository(
            client=client,
        )
    )

    try:
        subjects = repository.list_subjects()
        components = repository.list_components()
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "danh m\u1ee5c M\u00f4n/Ph\u00e2n m\u00f4n: "
            f"{error}"
        )
        return

    components_by_subject = {}

    for component in components:
        components_by_subject.setdefault(
            component.subject_id,
            [],
        ).append(component)

    # =========================================================
    # TAO MON MOI
    # =========================================================
    st.subheader(
        "T\u1ea1o m\u00f4n m\u1edbi"
    )

    create_columns = st.columns(
        [3.2, 2.0, 1.5, 0.9]
    )

    with create_columns[0]:
        new_subject_name = st.text_input(
            "T\u00ean m\u00f4n",
            key="admin_subject_new_name",
            placeholder="Nh\u1eadp t\u00ean m\u00f4n",
        ).strip()

    with create_columns[1]:
        new_subject_policy = st.selectbox(
            "Ph\u00e2n m\u00f4n",
            options=(
                SubjectComponentPolicy.OPTIONAL,
                SubjectComponentPolicy.NONE,
                SubjectComponentPolicy.REQUIRED,
            ),
            format_func=lambda value: {
                SubjectComponentPolicy.OPTIONAL:
                    "C\u00f3 th\u1ec3 ch\u1ecdn ph\u00e2n m\u00f4n",
                SubjectComponentPolicy.NONE:
                    "Kh\u00f4ng c\u00f3 ph\u00e2n m\u00f4n",
                SubjectComponentPolicy.REQUIRED:
                    "B\u1eaft bu\u1ed9c ch\u1ecdn ph\u00e2n m\u00f4n",
            }[value],
            key="admin_subject_new_policy",
        )

    with create_columns[2]:
        new_subject_status = st.selectbox(
            "Tr\u1ea1ng th\u00e1i",
            options=(
                CatalogStatus.ACTIVE,
                CatalogStatus.INACTIVE,
            ),
            format_func=lambda value: (
                "\u0110ang s\u1eed d\u1ee5ng"
                if value is CatalogStatus.ACTIVE
                else "Ng\u1eebng s\u1eed d\u1ee5ng"
            ),
            key="admin_subject_new_status",
        )

    with create_columns[3]:
        st.write("")
        st.write("")

        create_subject = st.button(
            "+",
            key="admin_subject_create",
            width="stretch",
            help="Th\u00eam m\u00f4n m\u1edbi",
        )

    if create_subject:
        try:
            if not new_subject_name:
                raise ValueError(
                    "T\u00ean m\u00f4n kh\u00f4ng "
                    "\u0111\u01b0\u1ee3c \u0111\u1ec3 tr\u1ed1ng."
                )

            repository.save_subject(
                subject=Subject(
                    subject_id=(
                        "subject-"
                        + uuid4().hex
                    ),
                    code=(
                        "SUB-"
                        + uuid4().hex[:8].upper()
                    ),
                    name=new_subject_name,
                    component_policy=(
                        new_subject_policy
                    ),
                    status=(
                        new_subject_status
                    ),
                    display_order=(
                        len(subjects) + 1
                    ),
                )
            )

        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 t\u1ea1o m\u00f4n: "
                f"{error}"
            )
        else:
            st.success(
                "\u0110\u00e3 t\u1ea1o m\u00f4n m\u1edbi."
            )
            st.rerun()

    st.divider()

    # =========================================================
    # DANH SACH MON + PHAN MON
    # =========================================================
    st.subheader(
        "Danh s\u00e1ch M\u00f4n & Ph\u00e2n m\u00f4n"
    )

    if not subjects:
        st.info(
            "Ch\u01b0a c\u00f3 m\u00f4n n\u00e0o."
        )
        return

    header = st.columns(
        [2.8, 2.0, 1.4, 0.8]
    )

    header[0].markdown(
        "**M\u00f4n**"
    )
    header[1].markdown(
        "**Ph\u00e2n m\u00f4n**"
    )
    header[2].markdown(
        "**Tr\u1ea1ng th\u00e1i**"
    )
    header[3].markdown(
        "**Thao t\u00e1c**"
    )

    for subject in subjects:
        subject_components = tuple(
            components_by_subject.get(
                subject.subject_id,
                (),
            )
        )

        subject_row = st.columns(
            [2.8, 2.0, 1.4, 0.8]
        )

        with subject_row[0]:
            edited_subject_name = st.text_input(
                "M\u00f4n",
                value=subject.name,
                key=(
                    "admin_subject_name_"
                    + subject.subject_id
                ),
                label_visibility="collapsed",
            )

        with subject_row[1]:
            subject_policy = st.selectbox(
                "Ch\u00ednh s\u00e1ch ph\u00e2n m\u00f4n",
                options=(
                    SubjectComponentPolicy.OPTIONAL,
                    SubjectComponentPolicy.NONE,
                    SubjectComponentPolicy.REQUIRED,
                ),
                index=(
                    (
                        SubjectComponentPolicy.OPTIONAL,
                        SubjectComponentPolicy.NONE,
                        SubjectComponentPolicy.REQUIRED,
                    ).index(
                        subject.component_policy
                    )
                ),
                format_func=lambda value: {
                    SubjectComponentPolicy.OPTIONAL:
                        "T\u00f9y ch\u1ecdn",
                    SubjectComponentPolicy.NONE:
                        "Kh\u00f4ng c\u00f3",
                    SubjectComponentPolicy.REQUIRED:
                        "B\u1eaft bu\u1ed9c",
                }[value],
                key=(
                    "admin_subject_policy_"
                    + subject.subject_id
                ),
                label_visibility="collapsed",
            )

        with subject_row[2]:
            subject_status = st.selectbox(
                "Tr\u1ea1ng th\u00e1i",
                options=(
                    CatalogStatus.ACTIVE,
                    CatalogStatus.INACTIVE,
                ),
                index=(
                    0
                    if subject.status
                    is CatalogStatus.ACTIVE
                    else 1
                ),
                format_func=lambda value: (
                    "ACTIVE"
                    if value is CatalogStatus.ACTIVE
                    else "INACTIVE"
                ),
                key=(
                    "admin_subject_status_"
                    + subject.subject_id
                ),
                label_visibility="collapsed",
            )

        with subject_row[3]:
            subject_actions = st.columns(2)

            with subject_actions[0]:
                save_subject = st.button(
                    "L\u01b0u",
                    key=(
                        "admin_subject_save_"
                        + subject.subject_id
                    ),
                    width="stretch",
                )

            with subject_actions[1]:
                delete_subject = st.button(
                    "X\u00f3a",
                    key=(
                        "admin_subject_delete_"
                        + subject.subject_id
                    ),
                    width="stretch",
                )

        if delete_subject:
            confirm_key = (
                "admin_subject_delete_confirm_"
                + subject.subject_id
            )

            if not st.session_state.get(
                confirm_key,
                False,
            ):
                st.session_state[
                    confirm_key
                ] = True

                st.warning(
                    "Nh\u1ea5n X\u00f3a l\u1ea7n n\u1eefa "
                    "\u0111\u1ec3 x\u00e1c nh\u1eadn x\u00f3a "
                    f"m\u00f4n {subject.name}."
                )

            else:
                try:
                    repository.delete_subject(
                        subject_id=(
                            subject.subject_id
                        )
                    )

                except Exception as error:
                    st.error(
                        "Kh\u00f4ng th\u1ec3 x\u00f3a m\u00f4n: "
                        f"{error}"
                    )

                else:
                    st.session_state.pop(
                        confirm_key,
                        None,
                    )

                    st.session_state[
                        "admin_subject_catalog_delete_success"
                    ] = True

                    st.rerun()

        if save_subject:
            try:
                repository.save_subject(
                    subject=Subject(
                        subject_id=subject.subject_id,
                        code=subject.code,
                        name=edited_subject_name,
                        component_policy=(
                            subject_policy
                        ),
                        status=subject_status,
                        display_order=(
                            subject.display_order
                        ),
                    )
                )
            except Exception as error:
                st.error(
                    "Kh\u00f4ng th\u1ec3 "
                    "c\u1eadp nh\u1eadt m\u00f4n: "
                    f"{error}"
                )
            else:
                st.success(
                    "\u0110\u00e3 c\u1eadp nh\u1eadt m\u00f4n."
                )
                st.rerun()

        # -----------------------------------------------------
        # CAC PHAN MON CUA MON
        # -----------------------------------------------------
        for component in subject_components:
            component_row = st.columns(
                [2.8, 2.0, 1.4, 0.8]
            )

            component_row[0].markdown(
                f"\u21b3 {subject.name}"
            )

            with component_row[1]:
                edited_component_name = st.text_input(
                    "Ph\u00e2n m\u00f4n",
                    value=component.name,
                    key=(
                        "admin_component_name_"
                        + component.component_id
                    ),
                    label_visibility="collapsed",
                )

            with component_row[2]:
                component_status = st.selectbox(
                    "Tr\u1ea1ng th\u00e1i",
                    options=(
                        CatalogStatus.ACTIVE,
                        CatalogStatus.INACTIVE,
                    ),
                    index=(
                        0
                        if component.status
                        is CatalogStatus.ACTIVE
                        else 1
                    ),
                    format_func=lambda value: (
                        "ACTIVE"
                        if value is CatalogStatus.ACTIVE
                        else "INACTIVE"
                    ),
                    key=(
                        "admin_component_status_"
                        + component.component_id
                    ),
                    label_visibility="collapsed",
                )

            with component_row[3]:
                component_actions = st.columns(2)

                with component_actions[0]:
                    save_component = st.button(
                        "L\u01b0u",
                        key=(
                            "admin_component_save_"
                            + component.component_id
                        ),
                        width="stretch",
                    )

                with component_actions[1]:
                    delete_component = st.button(
                        "X\u00f3a",
                        key=(
                            "admin_component_delete_"
                            + component.component_id
                        ),
                        width="stretch",
                    )

            if delete_component:
                confirm_key = (
                    "admin_component_delete_confirm_"
                    + component.component_id
                )

                if not st.session_state.get(
                    confirm_key,
                    False,
                ):
                    st.session_state[
                        confirm_key
                    ] = True

                    st.warning(
                        "Nh\u1ea5n X\u00f3a l\u1ea7n n\u1eefa "
                        "\u0111\u1ec3 x\u00e1c nh\u1eadn x\u00f3a "
                        f"ph\u00e2n m\u00f4n {component.name}."
                    )

                else:
                    try:
                        repository.delete_component(
                            component_id=(
                                component.component_id
                            )
                        )

                    except Exception as error:
                        st.error(
                            "Kh\u00f4ng th\u1ec3 "
                            "x\u00f3a ph\u00e2n m\u00f4n: "
                            f"{error}"
                        )

                    else:
                        st.session_state.pop(
                            confirm_key,
                            None,
                        )

                        st.session_state[
                            "admin_subject_catalog_delete_success"
                        ] = True

                        st.rerun()

            if save_component:
                try:
                    repository.save_component(
                        component=SubjectComponent(
                            component_id=(
                                component.component_id
                            ),
                            subject_id=(
                                component.subject_id
                            ),
                            code=component.code,
                            name=(
                                edited_component_name
                            ),
                            status=(
                                component_status
                            ),
                            display_order=(
                                component.display_order
                            ),
                            description=(
                                component.description
                            ),
                        )
                    )
                except Exception as error:
                    st.error(
                        "Kh\u00f4ng th\u1ec3 "
                        "c\u1eadp nh\u1eadt ph\u00e2n m\u00f4n: "
                        f"{error}"
                    )
                else:
                    st.success(
                        "\u0110\u00e3 c\u1eadp nh\u1eadt "
                        "ph\u00e2n m\u00f4n."
                    )
                    st.rerun()

        # -----------------------------------------------------
        # NUT + CUOI DONG DE THEM PHAN MON
        # -----------------------------------------------------
        add_row = st.columns(
            [2.8, 2.0, 1.4, 0.8]
        )

        add_row[0].markdown(
            f"\u21b3 {subject.name}"
        )

        with add_row[1]:
            new_component_name = st.text_input(
                "Ph\u00e2n m\u00f4n m\u1edbi",
                key=(
                    "admin_component_new_name_"
                    + subject.subject_id
                ),
                placeholder=(
                    "Nh\u1eadp ph\u00e2n m\u00f4n m\u1edbi"
                ),
                label_visibility="collapsed",
            ).strip()

        with add_row[2]:
            new_component_status = st.selectbox(
                "Tr\u1ea1ng th\u00e1i",
                options=(
                    CatalogStatus.ACTIVE,
                    CatalogStatus.INACTIVE,
                ),
                key=(
                    "admin_component_new_status_"
                    + subject.subject_id
                ),
                format_func=lambda value: (
                    "ACTIVE"
                    if value is CatalogStatus.ACTIVE
                    else "INACTIVE"
                ),
                label_visibility="collapsed",
            )

        with add_row[3]:
            add_component = st.button(
                "+",
                key=(
                    "admin_component_add_"
                    + subject.subject_id
                ),
                width="stretch",
                help=(
                    "Th\u00eam ph\u00e2n m\u00f4n "
                    f"cho {subject.name}"
                ),
            )

        if add_component:
            try:
                if not new_component_name:
                    raise ValueError(
                        "T\u00ean ph\u00e2n m\u00f4n "
                        "kh\u00f4ng \u0111\u01b0\u1ee3c "
                        "\u0111\u1ec3 tr\u1ed1ng."
                    )

                repository.save_component(
                    component=SubjectComponent(
                        component_id=(
                            "component-"
                            + uuid4().hex
                        ),
                        subject_id=(
                            subject.subject_id
                        ),
                        code=(
                            "COMP-"
                            + uuid4().hex[:8].upper()
                        ),
                        name=new_component_name,
                        status=(
                            new_component_status
                        ),
                        display_order=(
                            len(subject_components) + 1
                        ),
                        description=None,
                    )
                )

            except Exception as error:
                st.error(
                    "Kh\u00f4ng th\u1ec3 "
                    "th\u00eam ph\u00e2n m\u00f4n: "
                    f"{error}"
                )
            else:
                st.success(
                    "\u0110\u00e3 th\u00eam "
                    "ph\u00e2n m\u00f4n."
                )
                st.rerun()

        st.divider()
