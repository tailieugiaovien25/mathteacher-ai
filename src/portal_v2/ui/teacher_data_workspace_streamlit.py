from __future__ import annotations

from collections.abc import Callable

from educational_planning_v2.models.operational_data_source import (
    OperationalDataType,
)
from portal_v2.ui.teacher_data_workspace_portal import (
    TeacherDataWorkspaceItemState,
    TeacherDataWorkspaceViewModel,
)


def render_teacher_data_workspace(
    *,
    st,
    view: TeacherDataWorkspaceViewModel,
    on_ppct_update: Callable[[], None] | None = None,
) -> None:
    if not isinstance(
        view,
        TeacherDataWorkspaceViewModel,
    ):
        raise TypeError(
            "view must be TeacherDataWorkspaceViewModel"
        )

    if (
        on_ppct_update is not None
        and not callable(on_ppct_update)
    ):
        raise TypeError(
            "on_ppct_update must be callable or None"
        )

    st.title(
        "D\u1eef li\u1ec7u c\u1ee7a t\u00f4i"
    )

    st.caption(
        "Qu\u1ea3n l\u00fd d\u1eef li\u1ec7u d\u00f9ng chung "
        "cho c\u00e1c c\u00f4ng c\u1ee5 c\u1ee7a gi\u00e1o vi\u00ean."
    )

    st.subheader(
        f"N\u0103m h\u1ecdc: {view.academic_year}"
    )

    columns = st.columns(
        len(view.items)
    )

    for column, item in zip(
        columns,
        view.items,
    ):
        with column.container(
            border=True
        ):
            st.subheader(
                item.label
            )

            if (
                item.state
                is TeacherDataWorkspaceItemState.READY
            ):
                st.success(
                    "\u0110\u00e3 c\u00f3 d\u1eef li\u1ec7u"
                )

                st.write(
                    f"Ngu\u1ed3n: "
                    f"{item.source_name or item.source_id}"
                )

                st.write(
                    f"Phi\u00ean b\u1ea3n: "
                    f"{item.source_version or '\u2014'}"
                )

                st.write(
                    f"Tr\u1ea1ng th\u00e1i: "
                    f"{item.status.value if item.status else '\u2014'}"
                )

            else:
                st.warning(
                    "Ch\u01b0a c\u00f3 d\u1eef li\u1ec7u"
                )

                st.caption(
                    "H\u00e3y nh\u1eadp ho\u1eb7c t\u1ea3i "
                    "d\u1eef li\u1ec7u l\u00ean."
                )

            is_ppct = (
                item.data_type
                is OperationalDataType.PPCT
            )

            clicked = st.button(
                "C\u1eadp nh\u1eadt d\u1eef li\u1ec7u",
                key=(
                    "teacher_data_update_"
                    + item.data_type.value.lower()
                ),
                use_container_width=True,
                disabled=(
                    not is_ppct
                    or on_ppct_update is None
                ),
                help=(
                    None
                    if is_ppct
                    else (
                        "Ch\u1ee9c n\u0103ng n\u00e0y s\u1ebd "
                        "\u0111\u01b0\u1ee3c k\u00edch ho\u1ea1t "
                        "\u1edf b\u01b0\u1edbc ti\u1ebfp theo."
                    )
                ),
            )

            if (
                clicked
                and is_ppct
                and on_ppct_update is not None
            ):
                on_ppct_update()
