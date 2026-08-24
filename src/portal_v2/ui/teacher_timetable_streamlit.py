from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import uuid4

from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
    SupabaseSubjectCatalogRepository,
)
from educational_planning_v2.adapters.supabase_class_catalog_repository import (
    SupabaseClassCatalogRepository,
)
from educational_planning_v2.services.teacher_timetable_subject_scope_service import (
    TeacherTimetableSubjectScope,
)
from educational_planning_v2.services.teacher_timetable_assignment_bridge import (
    TeacherTimetableAssignmentBridge,
)

from educational_planning_v2.adapters.supabase_teacher_timetable_repository import (
    SupabaseTeacherTimetableRepository,
)
from educational_planning_v2.adapters.supabase_teaching_assignment_repository import (
    SupabaseTeachingAssignmentRepository,
)
from educational_planning_v2.adapters.supabase_teacher_profile_repository import (
    SupabaseTeacherProfileRepository,
)
from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
)
from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlot,
    TeacherTimetableSlotStatus,
    TeachingSession,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.services.teacher_timetable_service import (
    TeacherTimetableService,
)


from portal_v2.ui.portal_flash_feedback import (
    PortalFlashLevel,
    render_portal_flash,
    set_portal_flash,
)


_CATALOG_SNAPSHOT_SESSION_KEY = (
    "teacher_timetable_catalog_snapshot"
)
_TIMETABLE_DRAFT_KEY = "teacher_timetable_autosaved_draft"
_TIMETABLE_NOTICE_KEY = "teacher_timetable_floating_notice"


def _autosave_timetable_change(st, field_key: str, field_label: str) -> None:
    """Keep the latest timetable edit across reruns/page navigation."""
    draft = dict(st.session_state.get(_TIMETABLE_DRAFT_KEY, {}) or {})
    draft[field_key] = st.session_state.get(field_key)
    st.session_state[_TIMETABLE_DRAFT_KEY] = draft
    st.session_state[_TIMETABLE_NOTICE_KEY] = (
        f"Đã tự lưu thay đổi {field_label}."
    )


class _SubjectCatalogSnapshotRepository:
    def __init__(
        self,
        *,
        subjects,
        components,
    ) -> None:
        self._subjects = tuple(subjects)
        self._components = tuple(components)

    def list_subjects(
        self,
        *,
        status=None,
    ):
        return tuple(
            item
            for item in self._subjects
            if (
                status is None
                or item.status is status
            )
        )

    def list_components(
        self,
        *,
        subject_id=None,
        status=None,
    ):
        return tuple(
            item
            for item in self._components
            if (
                (
                    subject_id is None
                    or item.subject_id == subject_id
                )
                and (
                    status is None
                    or item.status is status
                )
            )
        )


_WEEKDAYS = (
    (1, "Th\u1ee9 2"),
    (2, "Th\u1ee9 3"),
    (3, "Th\u1ee9 4"),
    (4, "Th\u1ee9 5"),
    (5, "Th\u1ee9 6"),
    (6, "Th\u1ee9 7"),
    (7, "Ch\u1ee7 nh\u1eadt"),
)


def _assignment_label(
    assignment,
) -> str:
    parts = [
        assignment.class_id,
        assignment.subject_ref or "",
        assignment.component_ref or "",
    ]

    return " | ".join(
        part
        for part in parts
        if part
    )


def render_teacher_timetable(
    *,
    st,
    client: Any,
    user_id: str,
) -> None:

    render_portal_flash(
        st=st,
        session_state=st.session_state,
    )
    floating_notice = st.session_state.pop(_TIMETABLE_NOTICE_KEY, "")
    if floating_notice:
        st.toast(str(floating_notice), icon="💾")

    _perf_started = perf_counter()
    _perf: dict[str, float] = {}

    st.markdown(
        """
        <style>
        [data-testid="stHeader"] {height:2.6rem;min-height:2.6rem;background:rgba(255,255,255,.9);}
        .block-container {max-width: 1320px;padding-top:.35rem;padding-bottom:.8rem;}
        h1 {font-size: 1.72rem !important; letter-spacing: -.025em; color:#17233b;}
        .mt-timetable-hero {padding:.7rem 1rem;margin:0 0 .65rem;border:1px solid #8eacd0;border-radius:14px;background:linear-gradient(145deg,#fff,#eaf3ff);box-shadow:4px 5px 0 #b8c9dc,0 10px 22px rgba(38,70,116,.13),inset 0 1px 0 #fff;}
        .mt-timetable-hero h2 {margin:0;color:#142845;font:750 1.28rem/1.35 Inter,Arial,sans-serif;}
        .mt-timetable-hero p {margin:.18rem 0 0;color:#52647c;font:500 .86rem/1.35 Inter,Arial,sans-serif;}
        .mt-day-heading {display:flex;align-items:center;justify-content:space-between;padding:.2rem .15rem .7rem;border-bottom:1px solid #e5edf8;margin-bottom:.65rem;}
        .mt-day-heading strong {font:750 1.12rem/1.3 Inter,Arial,sans-serif;color:#17345f;}
        div[data-testid="stTabs"] button {font-weight:650;padding:.55rem .82rem;}
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:.35rem;background:#edf4fd;border-radius:14px;padding:.35rem;}
        div[data-testid="stTabs"] [aria-selected="true"] {background:#fff;border-radius:10px;box-shadow:0 4px 12px rgba(39,74,124,.12);}
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #dce7f5 !important;
            border-radius: 14px !important;
            box-shadow:4px 5px 0 #c4d2e3,0 9px 20px rgba(30,64,175,.10);
            background:linear-gradient(145deg,rgba(255,255,255,.96),rgba(237,245,255,.92));
            padding:.65rem .75rem!important;
        }

        div[data-testid="stSelectbox"] > div {
            border-radius: 8px;
        }

        div[data-baseweb="select"] > div {
            border: 1.5px solid #94a3b8 !important;
            min-height: 38px;height:38px;
            font-size:14px!important;
            background:#fff!important;
        }

        div[data-baseweb="select"]:focus-within > div {
            border: 2px solid #2563eb !important;
            box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.15);
        }

        hr {
            border-top: 2px solid #cbd5e1 !important;
            margin:.55rem 0!important;
        }
        .st-key-teacher_timetable_week_number {max-width:280px;margin-bottom:.25rem;}
        .st-key-teacher_timetable_save button {min-height:44px;border-radius:10px!important;box-shadow:3px 4px 0 #12345b!important;}
        div[data-testid="stAlert"] {margin:.45rem 0!important;}

        @media (max-width: 900px) {
            .block-container {
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="mt-timetable-hero">
          <h2>Thời khóa biểu</h2>
          <p>Mỗi ngày nằm trong một thẻ riêng; chọn lớp, môn và phân môn cho từng tiết rồi lưu một lần.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    profile_repository = (
        SupabaseTeacherProfileRepository(
            client,
            user_id,
        )
    )

    assignment_repository = (
        SupabaseTeachingAssignmentRepository(
            client,
            user_id,
        )
    )

    timetable_repository = (
        SupabaseTeacherTimetableRepository(
            client,
            user_id,
        )
    )

    subject_catalog_repository = (
        SupabaseSubjectCatalogRepository(
            client=client,
        )
    )

    try:
        _perf_step = perf_counter()
        profile = profile_repository.get()
        _perf["profile_load_ms"] = (
            perf_counter() - _perf_step
        ) * 1000
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

    academic_year = (
        profile.default_academic_year
    )

    st.subheader(
        f"N\u0103m h\u1ecdc: {academic_year}"
    )

    try:
        _perf_step = perf_counter()
        assignments = (
            assignment_repository.list_assignments(
                owner_id=user_id,
                academic_year=academic_year,
                role=TeachingAssignmentRole.TEACHING,
                status=TeachingAssignmentStatus.ACTIVE,
            )
        )
        _perf["assignments_load_ms"] = (
            perf_counter() - _perf_step
        ) * 1000
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            f"ph\u00e2n c\u00f4ng gi\u1ea3ng d\u1ea1y: {error}"
        )
        return

    if not assignments:
        st.info(
            "Ch\u01b0a c\u00f3 ph\u00e2n c\u00f4ng "
            "gi\u1ea3ng d\u1ea1y ACTIVE cho n\u0103m h\u1ecdc n\u00e0y."
        )
        return

    try:
        catalog_snapshot = st.session_state.get(
            _CATALOG_SNAPSHOT_SESSION_KEY
        )

        if (
            catalog_snapshot is None
            or not any(tuple(catalog_snapshot[0] or ()))
        ):
            _catalog_perf_step = perf_counter()

            snapshot_subjects = (
                subject_catalog_repository.list_subjects(
                    status=CatalogStatus.ACTIVE,
                )
            )

            snapshot_components = (
                subject_catalog_repository.list_components(
                    status=CatalogStatus.ACTIVE,
                )
            )

            catalog_snapshot = (
                snapshot_subjects,
                snapshot_components,
            )

            st.session_state[
                _CATALOG_SNAPSHOT_SESSION_KEY
            ] = catalog_snapshot

            _perf["catalog_snapshot_build_ms"] = (
                perf_counter() - _catalog_perf_step
            ) * 1000
        else:
            _perf["catalog_snapshot_build_ms"] = 0.0

        (
            snapshot_subjects,
            snapshot_components,
        ) = catalog_snapshot

        _perf_step = perf_counter()

        active_components_by_subject = {}

        for component in snapshot_components:
            if (
                component.status
                is not CatalogStatus.ACTIVE
            ):
                continue

            active_components_by_subject.setdefault(
                component.subject_id,
                [],
            ).append(
                component
            )

        subject_scopes_list = []

        for subject in snapshot_subjects:
            if (
                subject.status
                is not CatalogStatus.ACTIVE
            ):
                continue

            components = (
                active_components_by_subject.get(
                    subject.subject_id,
                    [],
                )
            )

            if components:
                for component in components:
                    subject_scopes_list.append(
                        TeacherTimetableSubjectScope(
                            subject_id=(
                                subject.subject_id
                            ),
                            subject_name=(
                                subject.name
                            ),
                            component_id=(
                                component.component_id
                            ),
                            component_name=(
                                component.name
                            ),
                        )
                    )
            else:
                subject_scopes_list.append(
                    TeacherTimetableSubjectScope(
                        subject_id=(
                            subject.subject_id
                        ),
                        subject_name=(
                            subject.name
                        ),
                        component_id=None,
                        component_name=None,
                    )
                )

        subject_scopes = tuple(
            subject_scopes_list
        )

        _perf["catalog_scopes_build_ms"] = (
            perf_counter() - _perf_step
        ) * 1000

    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "danh m\u1ee5c M\u00f4n/Ph\u00e2n m\u00f4n "
            f"canonical: {error}"
        )
        return

    if not subject_scopes:
        # A stale/temporarily empty catalogue must not blank the entire page.
        # Active teaching assignments already carry canonical IDs and provide
        # a safe display fallback until the catalogue is refreshed.
        subject_scopes = tuple(
            TeacherTimetableSubjectScope(
                subject_id=str(item.subject_ref or ""),
                subject_name=str(item.subject_ref or "Chưa xác định"),
                component_id=str(item.component_ref or "") or None,
                component_name=str(item.component_ref or "") or None,
            )
            for item in {
                (
                    str(assignment.subject_ref or ""),
                    str(assignment.component_ref or ""),
                ): assignment
                for assignment in assignments
                if str(assignment.subject_ref or "").strip()
            }.values()
        )
        st.toast(
            "Đang dùng dữ liệu Môn/Phân môn từ phân công giảng dạy; "
            "danh mục canonical sẽ được tải lại tự động.",
            icon="ℹ️",
        )

    _perf_step = perf_counter()

    canonical_assignment_options = (
        TeacherTimetableAssignmentBridge()
        .build_options(
            assignments=assignments,
            subject_scopes=subject_scopes,
        )
    )

    _perf["bridge_build_ms"] = (
        perf_counter() - _perf_step
    ) * 1000

    if not canonical_assignment_options:
        st.warning(
            "Kh\u00f4ng c\u00f3 ph\u00e2n c\u00f4ng "
            "gi\u1ea3ng d\u1ea1y ACTIVE n\u00e0o "
            "kh\u1edbp v\u1edbi danh m\u1ee5c "
            "M\u00f4n/Ph\u00e2n m\u00f4n canonical. "
            "H\u00e3y ki\u1ec3m tra l\u1ea1i "
            "Ph\u00e2n c\u00f4ng trong khu v\u1ef1c ADMIN."
        )
        return

    canonical_option_by_assignment_id = {
        item.assignment_id: item
        for item in canonical_assignment_options
    }

    with st.expander(
        "Timetable data diagnostics",
        expanded=False,
    ):
        st.markdown(
            "##### 1. Active teaching assignments"
        )

        st.dataframe(
            [
                {
                    "assignment_id": item.assignment_id,
                    "class_id": item.class_id,
                    "subject_ref": item.subject_ref,
                    "component_ref": item.component_ref,
                }
                for item in assignments
            ],
            use_container_width=True,
            hide_index=True,
        )


        st.markdown(
            "##### 1B. Full assignment details"
        )

        for item in assignments:
            st.code(
                "\n".join(
                    (
                        f"assignment_id={item.assignment_id}",
                        f"class_id={item.class_id}",
                        f"subject_ref={item.subject_ref}",
                        f"component_ref={item.component_ref}",
                        f"role={item.role.value}",
                        f"status={item.status.value}",
                        f"effective_from={item.effective_from}",
                        f"effective_to={item.effective_to}",
                        "-" * 60,
                    )
                ),
                language="text",
            )

        st.markdown(
            "##### 2. Canonical catalog scopes"
        )

        st.dataframe(
            [
                {
                    "subject_id": item.subject_id,
                    "subject_name": item.subject_name,
                    "component_id": item.component_id or "",
                    "component_name": item.component_name or "",
                }
                for item in subject_scopes
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown(
            "##### 3. Canonical bridge options"
        )

        st.dataframe(
            [
                {
                    "assignment_id": item.assignment_id,
                    "class_id": item.class_id,
                    "subject_id": item.subject_id,
                    "subject_name": item.subject_name,
                    "component_id": item.component_id or "",
                    "component_name": item.component_name or "",
                }
                for item in canonical_assignment_options
            ],
            use_container_width=True,
            hide_index=True,
        )

    assignment_by_id = {
        item.assignment_id: item
        for item in assignments
    }

    try:
        _perf_step = perf_counter()
        slots = timetable_repository.list_slots(
            owner_id=user_id,
            academic_year=academic_year,
            status=TeacherTimetableSlotStatus.ACTIVE,
        )
        _perf["timetable_slots_load_ms"] = (
            perf_counter() - _perf_step
        ) * 1000
    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            f"th\u1eddi kh\u00f3a bi\u1ec3u: {error}"
        )
        return

    _perf["total_data_load_ms"] = (
        perf_counter() - _perf_started
    ) * 1000

    with st.expander(
        "Performance audit - temporary",
        expanded=False,
    ):
        st.json(
            {
                key: round(value, 2)
                for key, value in _perf.items()
            }
        )

    st.caption(
        "M\u1ed7i \u00f4 ch\u1ecdn m\u1ed9t "
        "ph\u00e2n c\u00f4ng theo d\u1ea1ng "
        "L\u1edbp | M\u00f4n | Ph\u00e2n m\u00f4n."
    )

    slot_by_position = {
        (
            slot.weekday,
            slot.session,
            slot.period,
        ): slot
        for slot in slots
    }

    # =====================================================
    # CLASS CATALOG LABELS
    # class_id van la gia tri canonical dung de luu.
    # USER chi nhin thay ten/ma lop de doc.
    # =====================================================

    try:
        class_repository = (
            SupabaseClassCatalogRepository(
                client=client,
            )
        )

        class_catalog_items = (
            class_repository.list_classes(
                academic_year=academic_year,
            )
        )

    except Exception as error:
        st.error(
            "Kh\u00f4ng th\u1ec3 \u0111\u1ecdc "
            "danh m\u1ee5c l\u1edbp: "
            f"{error}"
        )
        return

    class_catalog_by_id = {
        item.class_id: item
        for item in class_catalog_items
    }

    class_options = (
        ("",)
        + tuple(
            dict.fromkeys(
                item.class_id
                for item in canonical_assignment_options
            )
        )
    )

    def class_name_for_id(
        class_id: str,
    ) -> str:
        if not class_id:
            return "\u2014 Tr\u1ed1ng \u2014"

        class_item = (
            class_catalog_by_id.get(
                class_id
            )
        )

        if class_item is None:
            # Bao toan du lieu TKB/phan cong cu.
            # Neu class_id cu khong con trong catalog,
            # van cho phep USER nhin thay gia tri do.
            return class_id

        class_code = (
            class_item.class_code.strip()
            if class_item.class_code
            else ""
        )

        class_name = (
            class_item.class_name.strip()
            if class_item.class_name
            else ""
        )

        # Neu Ten lop va Ma lop giong nhau,
        # chi hien mot gia tri.
        if (
            class_name
            and class_code
            and class_name.casefold()
            == class_code.casefold()
        ):
            return class_name

        # Uu tien Ten lop theo yeu cau giao dien USER.
        if class_name:
            return class_name

        if class_code:
            return class_code

        return class_id


    def options_for_class(
        class_id: str,
    ):
        if not class_id:
            return ()

        return tuple(
            item
            for item in canonical_assignment_options
            if item.class_id == class_id
        )

    def subject_ids_for_class(
        class_id: str,
    ) -> tuple[str, ...]:
        if not class_id:
            return ("",)

        return (
            ("",)
            + tuple(
                dict.fromkeys(
                    item.subject_id
                    for item in options_for_class(
                        class_id
                    )
                )
            )
        )

    def subject_name_for_id(
        class_id: str,
        subject_id: str,
    ) -> str:
        if not subject_id:
            return "\u2014 Tr\u1ed1ng \u2014"

        for item in options_for_class(
            class_id
        ):
            if item.subject_id == subject_id:
                return item.subject_name

        return subject_id

    def component_ids_for(
        class_id: str,
        subject_id: str,
    ) -> tuple[str, ...]:
        if (
            not class_id
            or not subject_id
        ):
            return ("",)

        values = []

        for item in options_for_class(
            class_id
        ):
            if (
                item.subject_id
                != subject_id
            ):
                continue

            if item.component_id is None:
                continue

            values.append(
                item.component_id
            )

        return (
            ("",)
            + tuple(
                dict.fromkeys(
                    values
                )
            )
        )

    def component_name_for_id(
        class_id: str,
        subject_id: str,
        component_id: str,
    ) -> str:
        if not component_id:
            return "\u2014 Tr\u1ed1ng \u2014"

        for item in options_for_class(
            class_id
        ):
            if (
                item.subject_id
                == subject_id
                and item.component_id
                == component_id
            ):
                return (
                    item.component_name
                    or component_id
                )

        return component_id

    def resolve_canonical_assignment_id(
        *,
        class_id: str,
        subject_id: str,
        component_id: str,
    ) -> str:
        if (
            not class_id
            or not subject_id
        ):
            return ""

        matches = [
            item
            for item in options_for_class(
                class_id
            )
            if (
                item.subject_id
                == subject_id
                and (
                    item.component_id
                    or ""
                )
                == (
                    component_id
                    or ""
                )
            )
        ]

        if len(matches) != 1:
            return ""

        return matches[0].assignment_id

    def normalized_widget_value(
        *,
        key: str,
        options: tuple[str, ...],
        default_value: str,
        auto_single: bool = False,
    ) -> str:
        current = st.session_state.get(
            key,
            default_value,
        )

        if current not in options:
            current = ""

        non_empty = tuple(
            value
            for value in options
            if value
        )

        if (
            auto_single
            and not current
            and len(non_empty) == 1
        ):
            current = non_empty[0]

        st.session_state[key] = current

        return current

    selections = {}
    incomplete_positions = []

    def render_period_row(
        *,
        weekday: int,
        session: TeachingSession,
        period: int,
    ) -> None:
        position = (
            weekday,
            session,
            period,
        )

        existing = slot_by_position.get(
            position
        )

        existing_assignment = (
            assignment_by_id.get(
                existing.assignment_id
            )
            if existing is not None
            else None
        )

        existing_canonical_option = (
            canonical_option_by_assignment_id.get(
                existing.assignment_id
            )
            if existing is not None
            else None
        )

        default_class = (
            existing_canonical_option.class_id
            if existing_canonical_option
            else ""
        )

        default_subject = (
            existing_canonical_option.subject_id
            if existing_canonical_option
            else ""
        )

        default_component = (
            (
                existing_canonical_option.component_id
                or ""
            )
            if existing_canonical_option
            else ""
        )

        key_prefix = (
            "teacher_timetable_"
            f"{session.value}_"
            f"{weekday}_"
            f"{period}"
        )

        class_key = (
            f"{key_prefix}_class"
        )

        subject_key = (
            f"{key_prefix}_subject"
        )

        component_key = (
            f"{key_prefix}_component"
        )

        selected_class = (
            normalized_widget_value(
                key=class_key,
                options=class_options,
                default_value=default_class,
            )
        )

        row = st.columns(
            [0.38, 0.9, 1.15, 1.35],
            gap="small",
        )

        row[0].markdown(
            f"**{period}**"
        )

        with row[1]:
            selected_class = st.selectbox(
                "L\u1edbp",
                options=class_options,
                format_func=(
                    class_name_for_id
                ),
                key=class_key,
                label_visibility="collapsed",
                on_change=_autosave_timetable_change,
                args=(st, class_key, "Lớp"),
            )

        subject_options = (
            subject_ids_for_class(
                selected_class
            )
        )

        subject_default = (
            default_subject
            if selected_class == default_class
            else ""
        )

        selected_subject = (
            normalized_widget_value(
                key=subject_key,
                options=subject_options,
                default_value=subject_default,
                auto_single=True,
            )
        )

        with row[2]:
            selected_subject = st.selectbox(
                "M\u00f4n",
                options=subject_options,
                format_func=(
                    lambda value:
                    subject_name_for_id(
                        selected_class,
                        value,
                    )
                ),
                key=subject_key,
                disabled=not selected_class,
                label_visibility="collapsed",
                on_change=_autosave_timetable_change,
                args=(st, subject_key, "Môn"),
            )

        component_options = (
            component_ids_for(
                selected_class,
                selected_subject,
            )
        )

        component_default = (
            default_component
            if (
                selected_class
                == default_class
                and selected_subject
                == default_subject
            )
            else ""
        )

        selected_component = (
            normalized_widget_value(
                key=component_key,
                options=component_options,
                default_value=component_default,
                auto_single=True,
            )
        )

        with row[3]:
            selected_component = (
                st.selectbox(
                    "Ph\u00e2n m\u00f4n",
                    options=component_options,
                    format_func=(
                        lambda value:
                        component_name_for_id(
                            selected_class,
                            selected_subject,
                            value,
                        )
                    ),
                    key=component_key,
                    disabled=(
                        not selected_subject
                    ),
                    label_visibility=(
                        "collapsed"
                    ),
                    on_change=_autosave_timetable_change,
                    args=(st, component_key, "Phân môn"),
                )
            )

        selected_assignment_id = (
            resolve_canonical_assignment_id(
                class_id=selected_class,
                subject_id=selected_subject,
                component_id=(
                    selected_component
                ),
            )
        )

        if (
            selected_class
            and not selected_assignment_id
        ):
            incomplete_positions.append(
                (
                    weekday,
                    session,
                    period,
                )
            )

        selections[position] = (
            selected_assignment_id
        )

    def render_day_session(
        *,
        weekday: int,
        session: TeachingSession,
        title: str,
    ) -> None:
        st.markdown(
            f"#### {title}"
        )

        header = st.columns(
            [0.38, 0.9, 1.15, 1.35],
            gap="small",
        )

        header[0].caption(
            "Ti\u1ebft"
        )
        header[1].caption(
            "L\u1edbp"
        )
        header[2].caption(
            "M\u00f4n"
        )
        header[3].caption(
            "Ph\u00e2n m\u00f4n"
        )

        for period in range(
            1,
            6,
        ):
            render_period_row(
                weekday=weekday,
                session=session,
                period=period,
            )

    def render_day_card(
        weekday: int,
        label: str,
    ) -> None:
        with st.container(
            border=True
        ):
            scheduled_count = sum(
                1
                for session in (
                    TeachingSession.MORNING,
                    TeachingSession.AFTERNOON,
                )
                for period in range(1, 6)
                if (weekday, session, period) in slot_by_position
            )
            st.markdown(
                "<div class='mt-day-heading'>"
                f"<strong>{label}</strong>"
                f"<span>{scheduled_count} tiết đã xếp</span>"
                "</div>",
                unsafe_allow_html=True,
            )

            render_day_session(
                weekday=weekday,
                session=(
                    TeachingSession.MORNING
                ),
                title="\u2600\ufe0f Bu\u1ed5i s\u00e1ng",
            )

            st.divider()

            render_day_session(
                weekday=weekday,
                session=(
                    TeachingSession.AFTERNOON
                ),
                title="\U0001f319 Bu\u1ed5i chi\u1ec1u",
            )

    st.markdown(
        "### Th\u1eddi kh\u00f3a bi\u1ec3u tu\u1ea7n"
    )

    st.caption(
        "M\u1ed7i ng\u00e0y l\u00e0 m\u1ed9t kh\u1ed1i "
        "ri\u00eang. Trong m\u1ed7i ti\u1ebft, "
        "ch\u1ecdn L\u1edbp \u2192 M\u00f4n "
        "\u2192 Ph\u00e2n m\u00f4n."
    )

    selected_week = st.selectbox(
        "Tu\u1ea7n h\u1ecdc",
        options=tuple(
            range(1, 41)
        ),
        format_func=lambda value: (
            f"Tu\u1ea7n {value}"
        ),
        key="teacher_timetable_week_number",
        on_change=_autosave_timetable_change,
        args=(st, "teacher_timetable_week_number", "Tuần học"),
    )

    st.caption(
        f"\u0110ang ch\u1ecdn: Tu\u1ea7n {selected_week}"
    )

    day_tabs = st.tabs(tuple(label for _, label in _WEEKDAYS))
    for day_tab, (weekday, label) in zip(day_tabs, _WEEKDAYS):
        with day_tab:
            render_day_card(weekday, label)

    st.caption(
        "L\u1edbp \u0111\u01b0\u1ee3c l\u1ecdc theo "
        "ph\u00e2n c\u00f4ng gi\u1ea3ng d\u1ea1y; "
        "M\u00f4n v\u00e0 Ph\u00e2n m\u00f4n "
        "\u0111\u01b0\u1ee3c l\u1ecdc theo "
        "danh m\u1ee5c canonical v\u00e0 "
        "\u0111\u0103ng k\u00fd c\u1ee7a gi\u00e1o vi\u00ean."
    )

    save_timetable = st.button(
        "C\u1eadp nh\u1eadt Th\u1eddi kh\u00f3a bi\u1ec3u",
        type="primary",
        width="stretch",
        key="teacher_timetable_save",
    )

    if save_timetable:
        if incomplete_positions:
            st.error(
                "Có tiết đã chọn Lớp "
                "nhưng chưa xác định được "
                "Môn/Phân môn hợp lệ. "
                "Hãy hoàn thành các ô "
                "trước khi lưu."
            )
            return

        timetable_service = (
            TeacherTimetableService(
                timetable_repository=(
                    timetable_repository
                ),
                assignment_repository=(
                    assignment_repository
                ),
            )
        )

        changed_count = 0

        try:
            for (
                weekday,
                session,
                period,
            ), selected_id in selections.items():
                position = (
                    weekday,
                    session,
                    period,
                )

                existing = (
                    slot_by_position.get(
                        position
                    )
                )

                if not selected_id:
                    if existing is not None:
                        timetable_repository.delete(
                            slot_id=(
                                existing.slot_id
                            )
                        )

                        changed_count += 1

                    continue

                assignment = (
                    assignment_by_id[
                        selected_id
                    ]
                )

                if (
                    existing is not None
                    and existing.assignment_id
                    == selected_id
                    and existing.effective_from
                    == assignment.effective_from
                    and existing.effective_to
                    == assignment.effective_to
                ):
                    continue

                slot = TeacherTimetableSlot(
                    slot_id=(
                        existing.slot_id
                        if existing is not None
                        else (
                            "tt-"
                            + uuid4().hex
                        )
                    ),
                    owner_id=user_id,
                    academic_year=academic_year,
                    assignment_id=(
                        selected_id
                    ),
                    weekday=weekday,
                    session=session,
                    period=period,
                    effective_from=(
                        assignment.effective_from
                    ),
                    effective_to=(
                        assignment.effective_to
                    ),
                    status=(
                        TeacherTimetableSlotStatus.ACTIVE
                    ),
                )

                timetable_service.save_slot(
                    slot=slot
                )

                changed_count += 1

        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 l\u01b0u "
                f"th\u1eddi kh\u00f3a bi\u1ec3u: {error}"
            )
            return

        if changed_count:
            set_portal_flash(
                st.session_state,
                message=(
                    "\u0110\u00e3 c\u1eadp nh\u1eadt "
                    f"{changed_count} thay \u0111\u1ed5i "
                    "Th\u1eddi kh\u00f3a bi\u1ec3u."
                ),
                level=PortalFlashLevel.SUCCESS,
            )
            st.toast(
                f"Đã lưu {changed_count} thay đổi Thời khóa biểu.",
                icon="✅",
            )
        else:
            set_portal_flash(
                st.session_state,
                message=(
                    "Th\u1eddi kh\u00f3a bi\u1ec3u "
                    "kh\u00f4ng c\u00f3 thay \u0111\u1ed5i."
                ),
                level=PortalFlashLevel.INFO,
            )
            st.toast(
                "Thời khóa biểu không có thay đổi mới.",
                icon="ℹ️",
            )

        st.rerun()
