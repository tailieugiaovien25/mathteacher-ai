from __future__ import annotations

import re
import streamlit as st

from lesson_planning_v2.services.canonical_lesson_plan_naming_service import (
    CanonicalLessonPlanNamingError,
    CanonicalLessonPlanNamingService,
)
from lesson_planning_v2.services.lesson_plan_preferred_filename_policy import (
    PreferredLessonPlanFilenameError,
    preferred_code_from_group,
    preferred_filename,
)

from educational_planning_v2.adapters.supabase_academic_week_repository import SupabaseAcademicWeekRepository
from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import SupabaseAcademicYearConfigurationRepository
from educational_planning_v2.adapters.supabase_subject_catalog_repository import SupabaseSubjectCatalogRepository
from educational_planning_v2.adapters.supabase_class_catalog_repository import SupabaseClassCatalogRepository
from lesson_planning_v2.services.weekly_lesson_plan_group_provider import (
    WeeklyLessonPlanGroupProvider,
    WeeklyLessonPlanGroupProviderError,
)
from portal_v2.context.session_scoped_context_holder import apply_canonical_year_week_change

_WEEK_KEY = "weekly_lesson_authoring_week_number"
_SELECTED_GROUP_KEY = "_v58_c5e4_selected_group_id"


def _text(value, fallback="—"):
    value = str(value or "").strip()
    return value or fallback


def _emit_week_change():
    selected_week = st.session_state.get(_WEEK_KEY)
    if selected_week is None:
        return
    user_id = str(st.session_state.get("portal_user_id", "") or "").strip()
    if not user_id:
        raise RuntimeError("CANONICAL_CONTEXT_USER_ID_REQUIRED")
    apply_canonical_year_week_change(
        st.session_state,
        user_id=user_id,
        field="week_number",
        value=int(selected_week),
        source_page="weekly_lesson_authoring",
        source_control=_WEEK_KEY,
    )


def _canonical_week(active_weeks):
    valid = tuple(int(item.week_number) for item in active_weeks)
    for key in (
        "global_weekly_active_week_number",
        "standardization_authoring_week_number",
        "lbg_user_week_number",
    ):
        try:
            value = int(st.session_state.get(key))
        except (TypeError, ValueError):
            continue
        if value in valid:
            return value
    return valid[0] if valid else None


def _occurrence_lines(group, *, client):
    result = []
    for item in tuple(getattr(group, "occurrences", ()) or ()):
        teaching_date = getattr(item, "teaching_date", None)
        date_text = (
            teaching_date.strftime("%d/%m/%Y")
            if hasattr(teaching_date, "strftime")
            else _text(teaching_date)
        )
        period = getattr(item, "timetable_period", None)
        suffix = f" · Tiết TKB: {period}" if period is not None else ""
        result.append(
            f"Lớp {_weekly_authoring_class_name(client=client, class_id=getattr(item, 'class_id', None))} · "
            f"Ngày dạy: {date_text}{suffix}"
        )
    return result


def _group_context_payload(group, *, client=None) -> dict:
    try:
        canonical_file_name = (
            CanonicalLessonPlanNamingService().expected_name(group).filename
        )
    except CanonicalLessonPlanNamingError:
        canonical_file_name = ""
    preferred_file_name = ""
    try:
        mode = str(getattr(getattr(group,"grouping_mode",None),"value",getattr(group,"grouping_mode","")) or "").upper()
        periods = tuple(int(x) for x in (getattr(group,"curriculum_periods",()) or ()) if int(x)>0)
        kwargs={"code":preferred_code_from_group(group),"grade":getattr(group,"grade",None)}
        if mode == "BY_WEEK":
            kwargs["week_number"]=getattr(group,"week_number",None)
        elif mode == "BY_LESSON":
            value=getattr(group,"lesson_number",None)
            if value is None:
                m=re.search(r"(\d+)",str(getattr(group,"lesson_id","") or ""))
                value=int(m.group(1)) if m else None
            kwargs["lesson_number"]=value
        elif periods:
            kwargs["curriculum_period"]=min(periods)
        preferred_file_name=preferred_filename(**kwargs).filename
    except (PreferredLessonPlanFilenameError,TypeError,ValueError):
        preferred_file_name=""
    canonical_group_name = (
        canonical_file_name[:-5]
        if canonical_file_name.lower().endswith(".docx")
        else canonical_file_name
    )
    occurrences = []
    for item in tuple(getattr(group, "occurrences", ()) or ()):
        teaching_date = getattr(item, "teaching_date", None)
        class_id = str(getattr(item, "class_id", "") or "")
        class_display = (
            _weekly_authoring_class_name(client=client, class_id=class_id)
            if client is not None
            else class_id
        )
        occurrences.append({
            "class_id": class_id,
            "class_display": class_display,
            "teaching_date": (
                teaching_date.isoformat()
                if hasattr(teaching_date, "isoformat")
                else str(teaching_date or "")
            ),
            "timetable_period": getattr(item, "timetable_period", None),
            "curriculum_period": getattr(item, "curriculum_period", None),
        })
    return {
        "schema_version": 1,
        "group_id": str(getattr(group, "group_id", "") or ""),
        "canonical_group_name": canonical_group_name,
        "canonical_file_name": canonical_file_name,
        "preferred_file_name": preferred_file_name,
        "academic_year": str(getattr(group, "academic_year", "") or ""),
        "week_number": getattr(group, "week_number", None),
        "subject_ref": str(getattr(group, "subject_ref", "") or ""),
        "subject_display": (
            _weekly_authoring_subject_name(
                client=client,
                subject_ref=str(getattr(group, "subject_ref", "") or ""),
            )
            if client is not None
            else str(getattr(group, "subject_ref", "") or "")
        ),
        "component_ref": str(getattr(group, "component_ref", "") or ""),
        "grade": str(getattr(group, "grade", "") or ""),
        "lesson_id": str(getattr(group, "lesson_id", "") or ""),
        "lesson_title": str(getattr(group, "lesson_title", "") or ""),
        "curriculum_periods": list(
            tuple(getattr(group, "curriculum_periods", ()) or ())
        ),
        "occurrences": occurrences,
    }


def _open_tool(group, target):
    payload = _group_context_payload(
        group,
        client=st.session_state.get("portal_supabase_client"),
    )
    st.session_state[_SELECTED_GROUP_KEY] = payload["group_id"]
    st.session_state["lesson_plan_group_context_v2"] = payload
    st.session_state["lesson_plan_group_context_read_only"] = True
    st.session_state["lesson_plan_group_navigation_target"] = target
    navigation_target = (
        "Soạn bài cùng chuẩn giáo án V2"
        if target == "Soạn bài cùng chuẩn giáo án"
        else target
    )
    st.session_state["portal_navigation_request"] = navigation_target


def _weekly_authoring_subject_name(*, client, subject_ref: str) -> str:
    normalized=str(subject_ref or "").strip()
    if not normalized:
        return ""
    try:
        for item in SupabaseSubjectCatalogRepository(client=client).list_subjects():
            if str(item.subject_id).strip() == normalized:
                return str(item.name).strip() or normalized
    except Exception:
        pass
    return normalized


def _weekly_authoring_class_name(*, client, class_id: str) -> str:
    normalized=str(class_id or "").strip()
    if not normalized:
        return ""
    try:
        item=SupabaseClassCatalogRepository(client=client).get(class_id=normalized)
        if item is not None:
            class_code=str(getattr(item, "class_code", "") or "").strip()
            class_name=str(getattr(item, "class_name", "") or "").strip()
            return class_code or class_name or normalized
    except Exception:
        pass
    return normalized


def _apply_weekly_authoring_modern_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stMainBlockContainer"] { max-width:1180px; padding-top:2rem; padding-bottom:4rem; }
        .mt-weekly-hero { padding:1.25rem 1.35rem; border:1px solid rgba(148,163,184,.24); border-radius:20px; background:rgba(255,255,255,.92); box-shadow:0 14px 40px rgba(15,23,42,.06); margin-bottom:1rem; }
        .mt-weekly-eyebrow { font-size:.78rem; font-weight:750; letter-spacing:.08em; text-transform:uppercase; color:#2563eb; margin-bottom:.3rem; }
        .mt-weekly-title { margin:0; font-size:2rem; line-height:1.15; letter-spacing:-.035em; color:#0f172a; }
        .mt-weekly-subtitle { margin:.55rem 0 0; max-width:760px; color:#64748b; font-size:.96rem; }
        .mt-section-title { display:flex; align-items:center; justify-content:space-between; gap:.75rem; margin:1.35rem 0 .35rem; }
        .mt-section-title h3 { margin:0; font-size:1.08rem; color:#0f172a; }
        .mt-section-title span { color:#64748b; font-size:.86rem; }
        [data-testid="stVerticalBlockBorderWrapper"] { border-radius:18px!important; border-color:rgba(148,163,184,.28)!important; background:rgba(255,255,255,.94); box-shadow:0 8px 26px rgba(15,23,42,.045); }
        div[data-testid="stButton"] button { min-height:2.65rem; border-radius:12px; font-weight:650; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_weekly_lesson_authoring_page(*, client, user_id: str) -> None:
    _apply_weekly_authoring_modern_styles()
    st.markdown(
        """
        <section class="mt-weekly-hero">
          <div class="mt-weekly-eyebrow">Không gian soạn bài</div>
          <h1 class="mt-weekly-title">Soạn bài theo tuần</h1>
          <p class="mt-weekly-subtitle">Chọn tuần soạn và xử lý từng nhóm giáo án từ Lịch báo giảng hiện tại. Tuần được đồng bộ hai chiều trong toàn hệ thống.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    current_year = SupabaseAcademicYearConfigurationRepository(
        client=client
    ).get_current()
    if current_year is None:
        st.warning("Chưa có năm học hiện hành.")
        return

    weeks = tuple(
        SupabaseAcademicWeekRepository(client=client).list_weeks(
            academic_year_id=current_year.academic_year_id
        )
    )
    active_weeks = tuple(
        item for item in weeks
        if str(
            getattr(
                getattr(item, "status", None),
                "value",
                getattr(item, "status", ""),
            )
        ).upper() == "ACTIVE"
    )
    if not active_weeks:
        st.warning("Năm học hiện hành chưa có tuần ACTIVE.")
        return

    week_numbers = tuple(int(item.week_number) for item in active_weeks)
    canonical_week = _canonical_week(active_weeks)
    if canonical_week is None:
        st.warning("Không xác định được tuần soạn.")
        return

    if st.session_state.get(_WEEK_KEY) != canonical_week:
        st.session_state[_WEEK_KEY] = canonical_week

    week_by_number = {int(item.week_number): item for item in active_weeks}
    st.selectbox(
        "Chọn tuần soạn",
        options=week_numbers,
        key=_WEEK_KEY,
        format_func=lambda value: (
            f"Tuần {value} "
            f"({week_by_number[value].start_date.strftime('%d/%m/%Y')} - "
            f"{week_by_number[value].end_date.strftime('%d/%m/%Y')})"
        ),
        on_change=_emit_week_change,
    )
    # G1B_WORKFLOW_STATE03_RUNTIME_WEEK_DIAGNOSTIC
    # Read-only observer. Never writes any week/context key.
    _g1b_ws03_user_id = str(st.session_state.get("portal_user_id", "") or "").strip()
    _g1b_ws03_canonical_week = None
    _g1b_ws03_error = ""
    if _g1b_ws03_user_id:
        try:
            from portal_v2.context.session_scoped_context_holder import get_canonical_context as _g1b_ws03_get_canonical_context
            _g1b_ws03_context = _g1b_ws03_get_canonical_context(
                st.session_state,
                user_id=_g1b_ws03_user_id,
                source_page="weekly_lesson_authoring",
            )
            _g1b_ws03_canonical_week = getattr(_g1b_ws03_context, "week_number", None)
        except Exception as _g1b_ws03_exc:
            _g1b_ws03_error = str(_g1b_ws03_exc)

    _g1b_ws03_snapshot = {
        "canonical_week": _g1b_ws03_canonical_week,
        "weekly_lesson_authoring_week_number": st.session_state.get(_WEEK_KEY),
        "global_weekly_active_week_number": st.session_state.get("global_weekly_active_week_number"),
        "standardization_authoring_week_number": st.session_state.get("standardization_authoring_week_number"),
        "lbg_user_week_number": st.session_state.get("lbg_user_week_number"),
        "system_weekly_week_number": st.session_state.get("system_weekly_week_number"),
        "error": _g1b_ws03_error,
    }
    st.info(
        "WORKFLOW-STATE-03 · Chẩn đoán tuần (chỉ đọc): "
        + "canonical=" + str(_g1b_ws03_snapshot["canonical_week"])
        + " · soạn-theo-tuần=" + str(_g1b_ws03_snapshot["weekly_lesson_authoring_week_number"])
        + " · global=" + str(_g1b_ws03_snapshot["global_weekly_active_week_number"])
        + " · chuẩn-hóa=" + str(_g1b_ws03_snapshot["standardization_authoring_week_number"])
        + " · LBG=" + str(_g1b_ws03_snapshot["lbg_user_week_number"])
        + " · system=" + str(_g1b_ws03_snapshot["system_weekly_week_number"])
        + ((" · diagnostic-error=" + _g1b_ws03_snapshot["error"]) if _g1b_ws03_snapshot["error"] else "")
    )

    selected_week = int(st.session_state[_WEEK_KEY])

    try:
        groups = WeeklyLessonPlanGroupProvider(
            client=client,
            user_id=str(user_id),
        ).provide(
            academic_year=str(current_year.academic_year),
            week_number=selected_week,
        )
    except WeeklyLessonPlanGroupProviderError as error:
        message = str(error)
        if message.startswith("CURRENT_LBG_NOT_FOUND"):
            st.info(
                f"Chưa có Lịch báo giảng đã cập nhật cho Tuần {selected_week}. "
                "Hãy cập nhật Lịch báo giảng trước."
            )
        elif "GROUPING_POLICY" in message:
            st.warning(
                "Chưa có cấu hình nhóm giáo án phù hợp từ ADMIN cho tuần này."
            )
            with st.expander("Chi tiết chẩn đoán cấu hình nhóm giáo án"):
                st.code(message)
                st.caption(
                    "Chẩn đoán chỉ đọc. Không thay đổi Lịch báo giảng hoặc cấu hình ADMIN."
                )
        else:
            st.error(f"Không thể tạo nhóm giáo án từ Lịch báo giảng: {message}")
        return

    st.markdown(
        f"""<div class="mt-section-title"><h3>Giáo án cần soạn</h3><span>Tuần {selected_week} · {len(groups)} nhóm giáo án</span></div>""",
        unsafe_allow_html=True,
    )
    if not groups:
        st.info(f"Lịch báo giảng Tuần {selected_week} chưa có tiết cần soạn.")
        return

    for group in groups:
        with st.container(border=True):
            cols = st.columns([2, 2, 2])
            with cols[0]:
                st.markdown(f"**Môn:** {_weekly_authoring_subject_name(client=client, subject_ref=group.subject_ref)}")
                component = _text(group.component_ref, fallback="")
                if component:
                    st.write(f"Phân môn: {component}")
                st.write(f"Khối: {_text(group.grade)}")
            with cols[1]:
                ppct = ", ".join(
                    str(x) for x in tuple(group.curriculum_periods or ())
                ) or "—"
                st.markdown(f"**Tiết PPCT:** {ppct}")
                st.write(f"Bài: {_text(group.lesson_title)}")
            with cols[2]:
                st.markdown(f"**Tuần:** {selected_week}")
                st.write(f"Năm học: {current_year.academic_year}")

            for line in _occurrence_lines(group, client=client):
                st.write(line)

            st.markdown(
                '<div class="mt-weekly-actions"></div>',
                unsafe_allow_html=True,
            )
            actions = st.columns(2)
            actions[0].button(
                "Soạn bài cùng chuẩn giáo án",
                key=f"weekly_standardize_{group.group_id}",
                use_container_width=True,
                on_click=_open_tool,
                args=(group, "Soạn bài cùng chuẩn giáo án"),
            )
            actions[1].button(
                "Soạn bài cùng AI",
                key=f"weekly_ai_{group.group_id}",
                use_container_width=True,
                on_click=_open_tool,
                args=(group, "Soạn bài cùng AI"),
            )
