from __future__ import annotations

from uuid import uuid4

from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
    SupabaseAcademicYearConfigurationRepository,
)
from educational_planning_v2.adapters.supabase_class_catalog_repository import (
    SupabaseClassCatalogRepository,
)
from educational_planning_v2.models.class_catalog import (
    ClassCatalog,
    ClassCatalogStatus,
)


_EDIT_CLASS_SESSION_KEY = (
    "admin_class_catalog_edit_id"
)


def _class_label(
    item: ClassCatalog,
) -> str:
    return (
        f"{item.class_code} | "
        f"{item.class_name} | "
        f"Kh\u1ed1i {item.grade_level}"
    )


def _show_class_delete_success_dialog(
    st,
) -> None:
    if not st.session_state.get(
        "admin_class_catalog_delete_success",
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
            key="admin_class_delete_dialog_close",
        ):
            st.session_state.pop(
                "admin_class_catalog_delete_success",
                None,
            )
            st.rerun()

    dialog()


def render_admin_class_catalog(
    st,
    *,
    client=None,
) -> None:
    st.title(
        "Danh s\u00e1ch l\u1edbp"
    )

    st.caption(
        "ADMIN qu\u1ea3n l\u00fd danh s\u00e1ch l\u1edbp linh ho\u1ea1t "
        "theo t\u1eebng n\u0103m h\u1ecdc. "
        "S\u1ed1 l\u01b0\u1ee3ng l\u1edbp v\u00e0 t\u00ean l\u1edbp kh\u00f4ng b\u1ecb "
        "hard-code trong h\u1ec7 th\u1ed1ng."
    )

    _show_class_delete_success_dialog(
        st,
    )

    if client is None:
        st.error(
            "Ch\u01b0a c\u00f3 k\u1ebft n\u1ed1i Supabase."
        )
        return

    year_repository = (
        SupabaseAcademicYearConfigurationRepository(
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
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc c\u1ea5u h\u00ecnh n\u0103m h\u1ecdc: "
            f"{error}"
        )
        return

    if current_year is None:
        st.warning(
            "Ch\u01b0a c\u00f3 n\u0103m h\u1ecdc hi\u1ec7n h\u00e0nh."
        )
        return

    academic_year = (
        current_year.academic_year
    )

    st.info(
        f"N\u0103m h\u1ecdc hi\u1ec7n h\u00e0nh: {academic_year}"
    )

    try:
        classes = (
            class_repository.list_classes(
                academic_year=academic_year,
            )
        )
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc danh s\u00e1ch l\u1edbp: "
            f"{error}"
        )
        return

    class_by_id = {
        item.class_id: item
        for item in classes
    }

    edit_class_id = (
        st.session_state.get(
            _EDIT_CLASS_SESSION_KEY
        )
    )

    edit_item = (
        class_by_id.get(
            edit_class_id
        )
        if edit_class_id
        else None
    )

    # =====================================================
    # ADD / UPDATE FORM
    # =====================================================

    st.subheader(
        "C\u1eadp nh\u1eadt danh m\u1ee5c l\u1edbp"
        if edit_item is not None
        else "Th\u00eam l\u1edbp"
    )

    with st.form(
        "admin_class_catalog_form"
    ):
        columns = st.columns(
            [1, 1.2, 2.2]
        )

        with columns[0]:
            grade_level = (
                st.text_input(
                    "Kh\u1ed1i",
                    value=(
                        edit_item.grade_level
                        if edit_item
                        else ""
                    ),
                    placeholder="V\u00ed d\u1ee5: 6",
                )
                .strip()
            )

        with columns[1]:
            class_code = (
                st.text_input(
                    "M\u00e3 l\u1edbp",
                    value=(
                        edit_item.class_code
                        if edit_item
                        else ""
                    ),
                    placeholder="V\u00ed d\u1ee5: 6A1",
                )
                .strip()
            )

        with columns[2]:
            class_name = (
                st.text_input(
                    "T\u00ean l\u1edbp",
                    value=(
                        edit_item.class_name
                        if edit_item
                        else ""
                    ),
                    placeholder=(
                        "V\u00ed d\u1ee5: L\u1edbp 6A1"
                    ),
                )
                .strip()
            )

        status = st.selectbox(
            "Tr\u1ea1ng th\u00e1i",
            options=(
                ClassCatalogStatus.ACTIVE,
                ClassCatalogStatus.INACTIVE,
            ),
            index=(
                0
                if (
                    edit_item is None
                    or edit_item.status
                    is ClassCatalogStatus.ACTIVE
                )
                else 1
            ),
            format_func=lambda value: (
                "\u0110ang s\u1eed d\u1ee5ng"
                if value
                is ClassCatalogStatus.ACTIVE
                else "Ng\u1eebng s\u1eed d\u1ee5ng"
            ),
        )

        action_columns = st.columns(
            2
            if edit_item is not None
            else 1
        )

        with action_columns[0]:
            submitted = (
                st.form_submit_button(
                    (
                        "L\u01b0u c\u1eadp nh\u1eadt"
                        if edit_item
                        else "Th\u00eam l\u1edbp"
                    ),
                    type="primary",
                    width="stretch",
                )
            )

        cancel_edit = False

        if edit_item is not None:
            with action_columns[1]:
                cancel_edit = (
                    st.form_submit_button(
                        "H\u1ee7y c\u1eadp nh\u1eadt",
                        width="stretch",
                    )
                )

    if cancel_edit:
        st.session_state[
            _EDIT_CLASS_SESSION_KEY
        ] = None
        st.rerun()

    if submitted:
        try:
            if not grade_level:
                raise ValueError(
                    "Kh\u1ed1i kh\u00f4ng \u0111\u01b0\u1ee3c \u0111\u1ec3 tr\u1ed1ng."
                )

            if not class_code:
                raise ValueError(
                    "M\u00e3 l\u1edbp kh\u00f4ng \u0111\u01b0\u1ee3c \u0111\u1ec3 tr\u1ed1ng."
                )

            if not class_name:
                raise ValueError(
                    "T\u00ean l\u1edbp kh\u00f4ng \u0111\u01b0\u1ee3c \u0111\u1ec3 tr\u1ed1ng."
                )

            existing_item = next(
                (
                    item
                    for item in classes
                    if (
                        item.academic_year
                        == academic_year
                        and item.class_code.casefold()
                        == class_code.casefold()
                    )
                ),
                None,
            )

            target_class_id = (
                edit_item.class_id
                if edit_item is not None
                else (
                    existing_item.class_id
                    if existing_item is not None
                    else (
                        "class-"
                        + uuid4().hex
                    )
                )
            )

            saved_item = (
                class_repository.save(
                    class_item=ClassCatalog(
                        class_id=target_class_id,
                        academic_year=(
                            academic_year
                        ),
                        grade_level=(
                            grade_level
                        ),
                        class_code=(
                            class_code
                        ),
                        class_name=(
                            class_name
                        ),
                        status=status,
                    )
                )
            )

        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 l\u01b0u l\u1edbp: "
                f"{error}"
            )
        else:
            st.session_state[
                _EDIT_CLASS_SESSION_KEY
            ] = None

            st.session_state.pop(
                "admin_class_catalog_manage_id",
                None,
            )
            st.session_state.pop(
                "admin_class_catalog_delete_confirm",
                None,
            )

            if (
                edit_item is not None
                or existing_item is not None
            ):
                st.success(
                    "\u0110\u00e3 c\u1eadp nh\u1eadt "
                    f"l\u1edbp {saved_item.class_name} "
                    "th\u00e0nh c\u00f4ng."
                )
            else:
                st.success(
                    "\u0110\u00e3 th\u00eam "
                    f"l\u1edbp {saved_item.class_name} "
                    "th\u00e0nh c\u00f4ng."
                )

            st.rerun()

    # =====================================================
    # CLASS LIST
    # =====================================================

    st.divider()

    st.subheader(
        f"Danh s\u00e1ch l\u1edbp n\u0103m h\u1ecdc "
        f"{academic_year}"
    )

    if not classes:
        st.info(
            "Ch\u01b0a c\u00f3 l\u1edbp n\u00e0o trong "
            "n\u0103m h\u1ecdc n\u00e0y."
        )
        return

    st.dataframe(
        [
            {
                "Kh\u1ed1i":
                    item.grade_level,
                "M\u00e3 l\u1edbp":
                    item.class_code,
                "T\u00ean l\u1edbp":
                    item.class_name,
                "Tr\u1ea1ng th\u00e1i": (
                    "\u0110ang s\u1eed d\u1ee5ng"
                    if item.status
                    is ClassCatalogStatus.ACTIVE
                    else "Ng\u1eebng s\u1eed d\u1ee5ng"
                ),
            }
            for item in classes
        ],
        width="stretch",
        hide_index=True,
    )

    # =====================================================
    # MANAGEMENT
    # =====================================================

    st.subheader(
        "Qu\u1ea3n l\u00fd l\u1edbp"
    )

    selected_class_id = (
        st.selectbox(
            "Ch\u1ecdn l\u1edbp",
            options=tuple(
                class_by_id.keys()
            ),
            format_func=lambda value: (
                _class_label(
                    class_by_id[value]
                )
            ),
            key=(
                "admin_class_catalog_manage_id"
            ),
        )
    )

    selected_item = (
        class_by_id[
            selected_class_id
        ]
    )

    action_columns = st.columns(3)

    with action_columns[0]:
        if st.button(
            "C\u1eadp nh\u1eadt",
            width="stretch",
            key=(
                "admin_class_catalog_edit"
            ),
        ):
            st.session_state[
                _EDIT_CLASS_SESSION_KEY
            ] = selected_class_id
            st.rerun()

    with action_columns[1]:
        target_status = (
            ClassCatalogStatus.INACTIVE
            if selected_item.status
            is ClassCatalogStatus.ACTIVE
            else ClassCatalogStatus.ACTIVE
        )

        if st.button(
            (
                "Ng\u1eebng s\u1eed d\u1ee5ng"
                if selected_item.status
                is ClassCatalogStatus.ACTIVE
                else "K\u00edch ho\u1ea1t l\u1ea1i"
            ),
            width="stretch",
            key=(
                "admin_class_catalog_toggle"
            ),
        ):
            try:
                class_repository.save(
                    class_item=ClassCatalog(
                        class_id=(
                            selected_item.class_id
                        ),
                        academic_year=(
                            selected_item.academic_year
                        ),
                        grade_level=(
                            selected_item.grade_level
                        ),
                        class_code=(
                            selected_item.class_code
                        ),
                        class_name=(
                            selected_item.class_name
                        ),
                        status=target_status,
                    )
                )
            except Exception as error:
                st.error(
                    "Kh\u00f4ng th\u1ec3 thay \u0111\u1ed5i "
                    "tr\u1ea1ng th\u00e1i l\u1edbp: "
                    f"{error}"
                )
            else:
                st.rerun()

    with action_columns[2]:
        confirm_key = (
            "admin_class_catalog_delete_confirm"
        )

        if st.session_state.get(
            confirm_key
        ) != selected_class_id:
            if st.button(
                "X\u00f3a",
                width="stretch",
                key=(
                    "admin_class_catalog_delete"
                ),
            ):
                st.session_state[
                    confirm_key
                ] = selected_class_id
                st.rerun()
        else:
            st.warning(
                "Nh\u1ea5n l\u1ea7n n\u1eefa \u0111\u1ec3 x\u00e1c nh\u1eadn x\u00f3a."
            )

            if st.button(
                "X\u00e1c nh\u1eadn x\u00f3a",
                width="stretch",
                type="primary",
                key=(
                    "admin_class_catalog_delete_confirm_button"
                ),
            ):
                try:
                    # ADMIN co quyen cao nhat:
                    # xoa cac phan cong dang tham chieu lop truoc.
                    (
                        client
                        .table("teaching_assignments")
                        .delete()
                        .eq(
                            "class_id",
                            selected_class_id,
                        )
                        .execute()
                    )

                    class_repository.delete(
                        class_id=(
                            selected_class_id
                        )
                    )

                except Exception as error:
                    st.error(
                        "Kh\u00f4ng th\u1ec3 x\u00f3a l\u1edbp: "
                        f"{error}"
                    )

                else:
                    st.session_state.pop(
                        confirm_key,
                        None,
                    )
                    st.session_state.pop(
                        "admin_class_catalog_manage_id",
                        None,
                    )
                    st.session_state[
                        _EDIT_CLASS_SESSION_KEY
                    ] = None
                    st.session_state[
                        "admin_class_catalog_delete_success"
                    ] = True

                    st.rerun()
