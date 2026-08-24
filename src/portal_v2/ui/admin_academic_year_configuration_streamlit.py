from __future__ import annotations

from datetime import date
from uuid import uuid4

from educational_planning_v2.adapters.supabase_academic_year_calendar_event_repository import (
    SupabaseAcademicYearCalendarEventRepository,
)
from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
    SupabaseAcademicYearConfigurationRepository,
)
from educational_planning_v2.adapters.supabase_academic_week_repository import (
    SupabaseAcademicWeekRepository,
)
from educational_planning_v2.models.academic_week_configuration import (
    AcademicWeekConfiguration,
    AcademicWeekStatus,
)
from educational_planning_v2.services.academic_week_configuration_service import (
    AcademicWeekConfigurationService,
)
from educational_planning_v2.models.academic_year_calendar_event import (
    AcademicYearCalendarEvent,
    AcademicYearCalendarEventStatus,
    AcademicYearCalendarEventType,
)
from educational_planning_v2.models.academic_year_configuration import (
    AcademicYearConfiguration,
    AcademicYearStatus,
    normalize_academic_year,
)


_EVENT_LABELS = {
    AcademicYearCalendarEventType.HOLIDAY:
        "\u004e\u0067\u0068\u1ec9 "
        "\u006c\u1ec5",
    AcademicYearCalendarEventType.TET_BREAK:
        "\u004e\u0067\u0068\u1ec9 "
        "\u0054\u1ebf\u0074",
    AcademicYearCalendarEventType.MIDTERM_BREAK:
        "\u004e\u0067\u0068\u1ec9 "
        "\u0067\u0069\u1eef\u0061 "
        "\u006b\u1ef3",
    AcademicYearCalendarEventType.MAKEUP_DAY:
        "\u0048\u1ecdc "
        "\u0062\u00f9",
    AcademicYearCalendarEventType.SCHOOL_EVENT:
        "\u0053\u1ef1 "
        "\u006b\u0069\u1ec7\u006e "
        "\u006e\u0068\u00e0 "
        "\u0074\u0072\u01b0\u1edd\u006e\u0067",
    AcademicYearCalendarEventType.OTHER_BREAK:
        "\u004e\u0067\u0068\u1ec9 "
        "\u006b\u0068\u00e1\u0063",
}


def render_admin_academic_year_configuration(
    st,
    *,
    client=None,
) -> None:
    st.title(
        "\u0043\u1ea5\u0075 "
        "\u0068\u00ec\u006e\u0068 "
        "\u006e\u0103\u006d "
        "\u0068\u1ecdc"
    )

    st.caption(
        "\u0051\u0075\u1ea3\u006e "
        "\u006c\u00fd "
        "\u006e\u0103\u006d "
        "\u0068\u1ecdc "
        "\u0068\u0069\u1ec7\u006e "
        "\u0068\u00e0\u006e\u0068, "
        "\u006e\u0067\u00e0\u0079 "
        "\u006b\u0068\u0061\u0069 "
        "\u0067\u0069\u1ea3\u006e\u0067, "
        "\u0068\u1ecdc "
        "\u006b\u1ef3 "
        "\u0076\u00e0 "
        "\u006c\u1ecb\u0063\u0068 "
        "\u006e\u0067\u0068\u1ec9/"
        "\u0068\u1ecdc "
        "\u0062\u00f9."
    )

    if client is None:
        st.error(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u006b\u1ebf\u0074 "
            "\u006e\u1ed1\u0069 "
            "\u0053\u0075\u0070\u0061\u0062\u0061\u0073\u0065."
        )
        return

    configuration_repository = (
        SupabaseAcademicYearConfigurationRepository(
            client=client,
        )
    )

    event_repository = (
        SupabaseAcademicYearCalendarEventRepository(
            client=client,
        )
    )

    try:
        current_configuration = (
            configuration_repository.get_current()
        )
        configurations = (
            configuration_repository.list_configurations()
        )
    except Exception as error:
        st.error(
            "\u004b\u0068\u00f4\u006e\u0067 "
            "\u0074\u0068\u1ec3 "
            "\u0111\u1ecdc "
            "\u0063\u1ea5\u0075 "
            "\u0068\u00ec\u006e\u0068 "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc: "
            f"{error}"
        )
        return

    if current_configuration is None:
        st.warning(
            "\u0048\u1ec7 "
            "\u0074\u0068\u1ed1\u006e\u0067 "
            "\u0063\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc "
            "\u0068\u0069\u1ec7\u006e "
            "\u0068\u00e0\u006e\u0068."
        )
    else:
        st.success(
            "\u004e\u0103\u006d "
            "\u0068\u1ecdc "
            "\u0068\u0069\u1ec7\u006e "
            "\u0068\u00e0\u006e\u0068: "
            f"{current_configuration.academic_year}"
        )

    st.subheader(
        "\u0043\u1ea5\u0075 "
        "\u0068\u00ec\u006e\u0068 "
        "\u006e\u0103\u006d "
        "\u0068\u1ecdc"
    )

    with st.form(
        "admin_academic_year_configuration_form"
    ):
        academic_year_input = st.text_input(
            "\u004e\u0103\u006d "
            "\u0068\u1ecdc",
            value=(
                current_configuration.academic_year
                if current_configuration is not None
                else "2026-2027"
            ),
            help=(
                "\u0110\u1ecb\u006e\u0068 "
                "\u0064\u1ea1\u006e\u0067 "
                "\u0063\u0068\u0075\u1ea9\u006e: "
                "YYYY-YYYY"
            ),
        )

        date_columns = st.columns(2)

        with date_columns[0]:
            start_date = st.date_input(
                "\u004e\u0067\u00e0\u0079 "
                "\u0062\u1eaft "
                "\u0111\u1ea7\u0075 "
                "\u006e\u0103\u006d "
                "\u0068\u1ecdc",
                value=(
                    current_configuration.start_date
                    if current_configuration is not None
                    else date(2026, 8, 24)
                ),
            )

        with date_columns[1]:
            end_date = st.date_input(
                "\u004e\u0067\u00e0\u0079 "
                "\u006b\u1ebf\u0074 "
                "\u0074\u0068\u00fa\u0063 "
                "\u006e\u0103\u006d "
                "\u0068\u1ecdc",
                value=(
                    current_configuration.end_date
                    if current_configuration is not None
                    else date(2027, 5, 31)
                ),
            )

        opening_ceremony_date = st.date_input(
            "\u004e\u0067\u00e0\u0079 "
            "\u006b\u0068\u0061\u0069 "
            "\u0067\u0069\u1ea3\u006e\u0067",
            value=(
                current_configuration.opening_ceremony_date
                if current_configuration is not None
                else date(2026, 9, 5)
            ),
        )

        st.markdown(
            "#### \u0048\u1ecdc "
            "\u006b\u1ef3 "
            "\u0049"
        )

        semester_1_columns = st.columns(2)

        with semester_1_columns[0]:
            semester_1_start = st.date_input(
                "\u0042\u1eaft "
                "\u0111\u1ea7\u0075 "
                "\u0048\u004b\u0049",
                value=(
                    current_configuration.semester_1_start
                    if current_configuration is not None
                    else date(2026, 8, 24)
                ),
            )

        with semester_1_columns[1]:
            semester_1_end = st.date_input(
                "\u004b\u1ebf\u0074 "
                "\u0074\u0068\u00fa\u0063 "
                "\u0048\u004b\u0049",
                value=(
                    current_configuration.semester_1_end
                    if current_configuration is not None
                    else date(2027, 1, 17)
                ),
            )

        st.markdown(
            "#### \u0048\u1ecdc "
            "\u006b\u1ef3 "
            "\u0049\u0049"
        )

        semester_2_columns = st.columns(2)

        with semester_2_columns[0]:
            semester_2_start = st.date_input(
                "\u0042\u1eaft "
                "\u0111\u1ea7\u0075 "
                "\u0048\u004b\u0049\u0049",
                value=(
                    current_configuration.semester_2_start
                    if current_configuration is not None
                    else date(2027, 1, 18)
                ),
            )

        with semester_2_columns[1]:
            semester_2_end = st.date_input(
                "\u004b\u1ebf\u0074 "
                "\u0074\u0068\u00fa\u0063 "
                "\u0048\u004b\u0049\u0049",
                value=(
                    current_configuration.semester_2_end
                    if current_configuration is not None
                    else date(2027, 5, 31)
                ),
            )

        status = st.selectbox(
            "\u0054\u0072\u1ea1\u006e\u0067 "
            "\u0074\u0068\u00e1\u0069",
            options=tuple(
                AcademicYearStatus
            ),
            index=(
                tuple(
                    AcademicYearStatus
                ).index(
                    current_configuration.status
                )
                if current_configuration is not None
                else tuple(
                    AcademicYearStatus
                ).index(
                    AcademicYearStatus.ACTIVE
                )
            ),
            format_func=lambda value: value.value,
        )

        set_as_current = st.checkbox(
            "\u0110\u1eb7\u0074 "
            "\u006c\u00e0\u006d "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc "
            "\u0068\u0069\u1ec7\u006e "
            "\u0068\u00e0\u006e\u0068",
            value=True,
        )

        save_configuration = st.form_submit_button(
            "\u004c\u01b0\u0075 "
            "\u0063\u1ea5\u0075 "
            "\u0068\u00ec\u006e\u0068 "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc",
            type="primary",
            use_container_width=True,
        )

    if save_configuration:
        try:
            canonical_year = (
                normalize_academic_year(
                    academic_year_input
                )
            )

            academic_year_id = (
                "AY-"
                + canonical_year
            )

            configuration = (
                AcademicYearConfiguration(
                    academic_year_id=(
                        academic_year_id
                    ),
                    academic_year=(
                        canonical_year
                    ),
                    start_date=start_date,
                    end_date=end_date,
                    opening_ceremony_date=(
                        opening_ceremony_date
                    ),
                    semester_1_start=(
                        semester_1_start
                    ),
                    semester_1_end=(
                        semester_1_end
                    ),
                    semester_2_start=(
                        semester_2_start
                    ),
                    semester_2_end=(
                        semester_2_end
                    ),
                    status=status,
                    is_current=False,
                )
            )

            configuration_repository.save(
                configuration=configuration,
            )

            if set_as_current:
                configuration_repository.set_current(
                    academic_year_id=(
                        academic_year_id
                    ),
                )

        except Exception as error:
            st.error(
                "\u004b\u0068\u00f4\u006e\u0067 "
                "\u0074\u0068\u1ec3 "
                "\u006c\u01b0\u0075 "
                "\u0063\u1ea5\u0075 "
                "\u0068\u00ec\u006e\u0068 "
                "\u006e\u0103\u006d "
                "\u0068\u1ecdc: "
                f"{error}"
            )
        else:
            st.success(
                "\u0110\u00e3 "
                "\u006c\u01b0\u0075 "
                "\u0063\u1ea5\u0075 "
                "\u0068\u00ec\u006e\u0068 "
                "\u006e\u0103\u006d "
                "\u0068\u1ecdc."
            )
            st.rerun()

    st.divider()

    st.subheader(
        "\u0044\u0061\u006e\u0068 "
        "\u0073\u00e1\u0063\u0068 "
        "\u006e\u0103\u006d "
        "\u0068\u1ecdc"
    )

    if not configurations:
        st.info(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u0063\u1ea5\u0075 "
            "\u0068\u00ec\u006e\u0068 "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc."
        )
    else:
        st.dataframe(
            [
                {
                    "\u004e\u0103\u006d "
                    "\u0068\u1ecdc":
                        item.academic_year,
                    "\u0054\u0072\u1ea1\u006e\u0067 "
                    "\u0074\u0068\u00e1\u0069":
                        item.status.value,
                    "\u0048\u0069\u1ec7\u006e "
                    "\u0068\u00e0\u006e\u0068":
                        item.is_current,
                    "\u004b\u0068\u0061\u0069 "
                    "\u0067\u0069\u1ea3\u006e\u0067":
                        item.opening_ceremony_date.isoformat(),
                }
                for item in configurations
            ],
            hide_index=True,
            use_container_width=True,
        )

    current_configuration = (
        configuration_repository.get_current()
    )

    # =====================================================
    # ADMIN ACADEMIC WEEK MANAGEMENT
    # =====================================================

    st.divider()

    st.subheader(
        "Qu\u1ea3n l\u00fd l\u1ecbch tu\u1ea7n"
    )

    st.caption(
        "ADMIN c\u00f3 quy\u1ec1n \u0111i\u1ec1u ch\u1ec9nh "
        "l\u1ecbch Tu\u1ea7n 1 \u0111\u1ebfn Tu\u1ea7n 40. "
        "Ch\u1ec9 c\u1ea7n \u0111\u1ed5i ng\u00e0y b\u1eaft \u0111\u1ea7u c\u1ee7a "
        "m\u1ed9t tu\u1ea7n; h\u1ec7 th\u1ed1ng s\u1ebd t\u1ef1 d\u1ecbch chuy\u1ec3n "
        "tu\u1ea7n \u0111\u00f3 v\u00e0 to\u00e0n b\u1ed9 c\u00e1c tu\u1ea7n ph\u00eda sau."
    )

    if current_configuration is None:
        st.warning(
            "H\u00e3y thi\u1ebft l\u1eadp n\u0103m h\u1ecdc "
            "hi\u1ec7n h\u00e0nh tr\u01b0\u1edbc khi "
            "qu\u1ea3n l\u00fd l\u1ecbch tu\u1ea7n."
        )

    else:
        week_repository = (
            SupabaseAcademicWeekRepository(
                client=client,
            )
        )

        week_service = (
            AcademicWeekConfigurationService(
                repository=week_repository,
            )
        )

        try:
            weeks = (
                week_service.ensure_weeks(
                    academic_year=(
                        current_configuration
                    )
                )
            )

        except Exception as error:
            st.error(
                "Kh\u00f4ng th\u1ec3 t\u1ea1o/\u0111\u1ecdc "
                "l\u1ecbch tu\u1ea7n: "
                f"{error}"
            )
            weeks = ()

        if weeks:
            st.markdown(
                f"**N\u0103m h\u1ecdc:** "
                f"{current_configuration.academic_year}"
            )

            st.dataframe(
                [
                    {
                        "Tu\u1ea7n":
                            item.week_number,

                        "T\u1eeb ng\u00e0y":
                            item.start_date.strftime(
                                "%d/%m/%Y"
                            ),

                        "\u0110\u1ebfn ng\u00e0y":
                            item.end_date.strftime(
                                "%d/%m/%Y"
                            ),

                        "Tr\u1ea1ng th\u00e1i":
                            item.status.value,

                        "\u0110i\u1ec1u ch\u1ec9nh ADMIN": (
                            "C\u00f3"
                            if item.is_manual_override
                            else "Kh\u00f4ng"
                        ),

                        "Ghi ch\u00fa":
                            item.note or "",
                    }
                    for item in weeks
                ],
                hide_index=True,
                width="stretch",
            )

            st.markdown(
                "#### \u0110i\u1ec1u ch\u1ec9nh tu\u1ea7n"
            )

            week_by_number = {
                item.week_number: item
                for item in weeks
            }

            selected_week_number = (
                st.selectbox(
                    "Ch\u1ecdn tu\u1ea7n",
                    options=tuple(
                        week_by_number.keys()
                    ),
                    format_func=lambda value: (
                        f"Tu\u1ea7n {value}"
                    ),
                    key=(
                        "admin_academic_week_number"
                    ),
                )
            )

            selected_week = (
                week_by_number[
                    selected_week_number
                ]
            )

            with st.form(
                "admin_academic_week_edit_form"
            ):
                week_start_date = st.date_input(
                    "Ngày bắt đầu mới",
                    value=selected_week.start_date,
                    key="admin_week_start_date",
                    help=(
                        "Ngày kết thúc và các tuần phía sau "
                        "được hệ thống tự động tính lại."
                    ),
                )

                shifted_week_end = (
                    selected_week.end_date
                    + (week_start_date - selected_week.start_date)
                )
                st.caption(
                    "Khoảng mới của Tuần "
                    f"{selected_week.week_number}: "
                    f"{week_start_date.strftime('%d/%m/%Y')} – "
                    f"{shifted_week_end.strftime('%d/%m/%Y')}"
                )

                week_status = st.selectbox(
                    "Tr\u1ea1ng th\u00e1i",
                    options=tuple(
                        AcademicWeekStatus
                    ),
                    index=tuple(
                        AcademicWeekStatus
                    ).index(
                        selected_week.status
                    ),
                    format_func=lambda value: (
                        value.value
                    ),
                    key=(
                        "admin_week_status"
                    ),
                )

                week_note = st.text_area(
                    "Ghi ch\u00fa",
                    value=(
                        selected_week.note
                        or ""
                    ),
                    key=(
                        "admin_week_note"
                    ),
                )

                update_week = (
                    st.form_submit_button(
                        "C\u1eadp nh\u1eadt tu\u1ea7n",
                        type="primary",
                        width="stretch",
                    )
                )

            if update_week:
                try:
                    selected_week_with_metadata = AcademicWeekConfiguration(
                        academic_week_id=selected_week.academic_week_id,
                        academic_year_id=selected_week.academic_year_id,
                        academic_year=selected_week.academic_year,
                        week_number=selected_week.week_number,
                        start_date=selected_week.start_date,
                        end_date=selected_week.end_date,
                        status=week_status,
                        is_manual_override=selected_week.is_manual_override,
                        note=week_note.strip() or None,
                    )
                    cascade_source_weeks = tuple(
                        selected_week_with_metadata
                        if item.week_number == selected_week.week_number
                        else item
                        for item in weeks
                    )
                    week_service.shift_from_week(
                        weeks=cascade_source_weeks,
                        week_number=selected_week.week_number,
                        new_start_date=week_start_date,
                    )

                except Exception as error:
                    st.error(
                        "Kh\u00f4ng th\u1ec3 c\u1eadp nh\u1eadt "
                        f"tu\u1ea7n: {error}"
                    )

                else:
                    st.success(
                        "\u0110\u00e3 c\u1eadp nh\u1eadt "
                        f"Tu\u1ea7n "
                        f"{selected_week.week_number} và các tuần phía sau."
                    )

                    st.rerun()


    st.divider()

    st.subheader(
        "\u004c\u1ecb\u0063\u0068 "
        "\u006e\u0067\u0068\u1ec9 "
        "\u0076\u00e0 "
        "\u0068\u1ecdc "
        "\u0062\u00f9"
    )

    if current_configuration is None:
        st.warning(
            "\u0048\u00e3\u0079 "
            "\u0074\u0068\u0069\u1ebf\u0074 "
            "\u006c\u1ead\u0070 "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc "
            "\u0068\u0069\u1ec7\u006e "
            "\u0068\u00e0\u006e\u0068 "
            "\u0074\u0072\u01b0\u1edb\u0063."
        )
        return

    with st.form(
        "admin_academic_year_calendar_event_form"
    ):
        event_type = st.selectbox(
            "\u004c\u006f\u1ea1\u0069 "
            "\u0073\u1ef1 "
            "\u006b\u0069\u1ec7\u006e",
            options=tuple(
                AcademicYearCalendarEventType
            ),
            format_func=lambda value: (
                _EVENT_LABELS[value]
            ),
        )

        event_name = st.text_input(
            "\u0054\u00ea\u006e "
            "\u0073\u1ef1 "
            "\u006b\u0069\u1ec7\u006e",
        )

        event_date_columns = st.columns(2)

        with event_date_columns[0]:
            event_start_date = st.date_input(
                "\u0054\u1eeb "
                "\u006e\u0067\u00e0\u0079",
                value=(
                    current_configuration.start_date
                ),
                key=(
                    "academic_year_event_start"
                ),
            )

        with event_date_columns[1]:
            event_end_date = st.date_input(
                "\u0110\u1ebf\u006e "
                "\u006e\u0067\u00e0\u0079",
                value=(
                    current_configuration.start_date
                ),
                key=(
                    "academic_year_event_end"
                ),
            )

        event_note = st.text_area(
            "\u0047\u0068\u0069 "
            "\u0063\u0068\u00fa",
        )

        save_event = st.form_submit_button(
            "\u0054\u0068\u00ea\u006d "
            "\u0076\u00e0\u006f "
            "\u006c\u1ecb\u0063\u0068 "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc",
            type="primary",
            use_container_width=True,
        )

    if save_event:
        try:
            if not event_name.strip():
                raise ValueError(
                    "\u0054\u00ea\u006e "
                    "\u0073\u1ef1 "
                    "\u006b\u0069\u1ec7\u006e "
                    "\u006b\u0068\u00f4\u006e\u0067 "
                    "\u0111\u01b0\u1ee3\u0063 "
                    "\u0111\u1ec3 "
                    "\u0074\u0072\u1ed1\u006e\u0067."
                )

            if (
                event_start_date
                < current_configuration.start_date
                or event_end_date
                > current_configuration.end_date
            ):
                raise ValueError(
                    "\u0053\u1ef1 "
                    "\u006b\u0069\u1ec7\u006e "
                    "\u0070\u0068\u1ea3\u0069 "
                    "\u006e\u1eb1\u006d "
                    "\u0074\u0072\u006f\u006e\u0067 "
                    "\u0070\u0068\u1ea1\u006d "
                    "\u0076\u0069 "
                    "\u006e\u0103\u006d "
                    "\u0068\u1ecdc."
                )

            event_repository.save(
                event=(
                    AcademicYearCalendarEvent(
                        event_id=(
                            "aye-"
                            + uuid4().hex
                        ),
                        academic_year_id=(
                            current_configuration.academic_year_id
                        ),
                        event_type=event_type,
                        name=event_name,
                        start_date=(
                            event_start_date
                        ),
                        end_date=(
                            event_end_date
                        ),
                        is_teaching_day_override=(
                            event_type
                            is AcademicYearCalendarEventType.MAKEUP_DAY
                        ),
                        note=(
                            event_note
                            or None
                        ),
                        status=(
                            AcademicYearCalendarEventStatus.ACTIVE
                        ),
                    )
                )
            )

        except Exception as error:
            st.error(
                "\u004b\u0068\u00f4\u006e\u0067 "
                "\u0074\u0068\u1ec3 "
                "\u006c\u01b0\u0075 "
                "\u0073\u1ef1 "
                "\u006b\u0069\u1ec7\u006e: "
                f"{error}"
            )
        else:
            st.success(
                "\u0110\u00e3 "
                "\u0074\u0068\u00ea\u006d "
                "\u0073\u1ef1 "
                "\u006b\u0069\u1ec7\u006e "
                "\u0076\u00e0\u006f "
                "\u006c\u1ecb\u0063\u0068 "
                "\u006e\u0103\u006d "
                "\u0068\u1ecdc."
            )
            st.rerun()

    try:
        events = event_repository.list_events(
            academic_year_id=(
                current_configuration.academic_year_id
            ),
            status=(
                AcademicYearCalendarEventStatus.ACTIVE
            ),
        )
    except Exception as error:
        st.error(
            "\u004b\u0068\u00f4\u006e\u0067 "
            "\u0074\u0068\u1ec3 "
            "\u0111\u1ecdc "
            "\u006c\u1ecb\u0063\u0068 "
            "\u006e\u0103\u006d "
            "\u0068\u1ecdc: "
            f"{error}"
        )
        return

    if not events:
        st.info(
            "\u0043\u0068\u01b0\u0061 "
            "\u0063\u00f3 "
            "\u006e\u0067\u00e0\u0079 "
            "\u006e\u0067\u0068\u1ec9 "
            "\u0068\u006f\u1eb7\u0063 "
            "\u0068\u1ecdc "
            "\u0062\u00f9."
        )
        return

    st.dataframe(
        [
            {
                "\u004c\u006f\u1ea1\u0069":
                    _EVENT_LABELS[
                        item.event_type
                    ],
                "\u0054\u00ea\u006e":
                    item.name,
                "\u0054\u1eeb":
                    item.start_date.isoformat(),
                "\u0110\u1ebf\u006e":
                    item.end_date.isoformat(),
                "\u0048\u1ecdc "
                "\u0062\u00f9":
                    item.is_teaching_day_override,
                "\u0047\u0068\u0069 "
                "\u0063\u0068\u00fa":
                    item.note or "",
            }
            for item in events
        ],
        hide_index=True,
        use_container_width=True,
    )
