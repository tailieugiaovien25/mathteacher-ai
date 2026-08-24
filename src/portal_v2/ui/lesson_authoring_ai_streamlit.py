"""Full-screen AI-assisted lesson-plan authoring page."""

from __future__ import annotations

import os
from datetime import date
from datetime import datetime
from hashlib import sha256
from html import escape
from typing import Any

import streamlit as st


CONTEXT_KEY = "lesson_authoring_ai_context"
DOCUMENT_KEY = "lesson_authoring_ai_document"
PENDING_DOCUMENT_KEY = "lesson_authoring_ai_pending_document"
SOURCE_BYTES_KEY = "lesson_authoring_ai_source_bytes"
SOURCE_NAME_KEY = "lesson_authoring_ai_source_name"
UPLOAD_HASH_KEY = "lesson_authoring_ai_upload_hash"
UNDO_KEY = "lesson_authoring_ai_undo"
SAVED_KEY = "lesson_authoring_ai_saved_document"
MANAGEMENT_CATALOG_KEY = "lesson_plan_management_catalog"
WORKING_CONTEXT_KEY = "lesson_authoring_working_context"
RESTORE_CONTEXT_KEY = "lesson_authoring_restore_context_to_standardization"
NAVIGATION_NOTICE_KEY = "lesson_authoring_navigation_notice"
AI_AUTOSAVE_NOTICE_KEY = "lesson_authoring_ai_autosave_notice"
AI_CONTEXT_DRAFT_KEY = "lesson_authoring_ai_autosaved_context"


_PAGE_CSS = r"""
<style>
.block-container {
  max-width: none !important;
  padding: .65rem 1rem 1rem !important;
}
[data-testid="stMainBlockContainer"] { max-width: none !important; }
.stApp, .stApp button, .stApp input, .stApp textarea,
.stApp select, .stApp label, .stApp p, .stApp span {
  font-size:16px;
  line-height:1.5;
}
.mt-ai-page-header {
  display:flex; align-items:center; justify-content:space-between; gap:1rem;
  padding:.8rem 1rem; border:2px solid #12345b; border-radius:12px;
  background:#071a33;
  color:#ffffff;
  box-shadow:4px 5px 0 #0a2342, 0 10px 24px rgba(10,35,66,.16);
  margin:0 5px .95rem 0;
}
.mt-ai-page-title { margin:0; font-size:23px; line-height:1.4; color:#ffffff; font-weight:800; }
.mt-ai-page-subtitle { margin:.12rem 0 0; color:#dbeafe; font-size:15px; line-height:1.4; }
.mt-ai-status { padding:.42rem .7rem; border-radius:3px; background:#071a33;
  border:2px solid #ffffff; color:#ffffff; font-weight:800; white-space:nowrap;
  box-shadow:2px 3px 0 #0a2342; }
.mt-ai-context-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
  gap:0; border:2px solid #12345b; background:#071a33; margin:0 4px 1rem 0;
  box-shadow:3px 4px 0 #0a2342; }
.mt-ai-context-item { background:#071a33; padding:.55rem .7rem; min-height:58px;
  border-right:1px solid #58718f; }
.mt-ai-context-item:last-child { border-right:0; }
.mt-ai-context-label { color:#bfdbfe; font-size:14px; line-height:1.4; font-weight:800; letter-spacing:.05em; }
.mt-ai-context-value { color:#ffffff; font-size:16px; line-height:1.4; font-weight:750; margin-top:.12rem;
  overflow:visible; text-overflow:clip; white-space:normal; overflow-wrap:anywhere; word-break:break-word; }
.mt-pane-label { font-size:16px; line-height:1.4; font-weight:900; letter-spacing:.06em; color:#ffffff;
  margin:.15rem 0 .35rem; }
.mt-ai-page-note { border:1px solid #365b85; background:transparent;
  padding:.55rem .7rem; font-size:13px; color:#29496d; box-shadow:2px 2px 0 #b7c5d5; }

/* Three primary work panes: navy 3D frame, no filled surface. */
div[data-testid="column"]:has(.mt-pane-label) {
  border:2px solid #12345b;
  border-radius:12px;
  background:#071a33 !important;
  box-shadow:4px 5px 0 #0a2342, 0 9px 18px rgba(10,35,66,.13);
  padding:.75rem .8rem 1rem;
  margin:0 5px 7px 0;
}

[data-testid="stExpander"] {
  background:#071a33 !important;
  color:#ffffff !important;
  border:2px solid #12345b !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] label,
[data-testid="stExpander"] [data-testid="stCaptionContainer"] {
  color:#ffffff !important;
  font-size:16px !important;
  line-height:1.5 !important;
}

/* Input surfaces intentionally remain unfilled/transparent. */
.stTextArea textarea,
.stTextInput input,
[data-baseweb="select"] > div,
[data-testid="stDateInput"] input,
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploaderDropzone"] section {
  background:transparent !important;
  background-color:transparent !important;
  border-color:#365b85 !important;
  color:#102f54 !important;
}
.stTextArea textarea {
  border:1.5px solid #365b85 !important;
  border-radius:2px !important;
  font-size:18px !important;
  line-height:1.5 !important;
  box-shadow:inset 0 0 0 1px rgba(18,52,91,.08) !important;
}
/* The full-document editor uses a translucent white paper surface. */
div[data-testid="column"]:has(.mt-ai-document-pane-marker) {
  background:#071a33 !important;
  border-color:#0a2a50 !important;
  box-shadow:5px 6px 0 #03101f, 0 12px 26px rgba(3,16,31,.28) !important;
}
div[data-testid="column"]:has(.mt-ai-document-pane-marker) .mt-pane-label {
  color:#f8fafc !important;
}
div[data-testid="column"]:has(.mt-ai-document-pane-marker) .stTextArea textarea {
  background:rgba(255,255,255,.94) !important;
  background-color:rgba(255,255,255,.94) !important;
  backdrop-filter:blur(10px);
  -webkit-backdrop-filter:blur(10px);
  font-size:18px !important;
  line-height:1.5 !important;
}
.stTextInput input:disabled,
[data-testid="stDateInput"] input:disabled {
  -webkit-text-fill-color:#102f54 !important;
  opacity:1 !important;
}
[class*="st-key-ai_"] input {
  min-height:42px !important;
  height:42px !important;
  font-size:15px !important;
  line-height:1.25 !important;
}
.stButton > button,
.stDownloadButton > button {
  border:1.5px solid #12345b !important;
  border-radius:9px !important;
  background:linear-gradient(145deg,#ffffff,#e8f2ff) !important;
  color:#0a2a50 !important;
  box-shadow:2px 3px 0 #12345b !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
  transform:translate(1px,1px);
  box-shadow:1px 2px 0 #12345b !important;
}
@media(max-width:1000px){.mt-ai-context-grid{grid-template-columns:repeat(3,1fr)}}
</style>
"""


def _value(context: dict[str, Any], name: str, fallback: str = "-") -> str:
    raw = context.get(name)
    if raw is None or raw == "":
        return fallback
    if isinstance(raw, (tuple, list)):
        return ", ".join(str(item) for item in raw) or fallback
    if hasattr(raw, "strftime"):
        return raw.strftime("%d/%m/%Y")
    return str(raw)


def _autosave_ai_document() -> None:
    """Save the current editor value whenever the user commits an edit."""
    document = str(st.session_state.get(DOCUMENT_KEY, "") or "")
    st.session_state[SAVED_KEY] = document
    st.session_state[AI_AUTOSAVE_NOTICE_KEY] = (
        "Đã tự lưu thay đổi của bài đang soạn."
    )


def _notify_ai_context_change(field_label: str) -> None:
    st.session_state[AI_CONTEXT_DRAFT_KEY] = dict(
        st.session_state.get(CONTEXT_KEY, {}) or {}
    )
    st.session_state[AI_AUTOSAVE_NOTICE_KEY] = (
        f"Đã tự lưu thay đổi {field_label} trên trang Soạn bài cùng AI."
    )


def _secret(name: str, fallback: str = "") -> str:
    try:
        value = st.secrets.get(name, fallback)
    except Exception:
        value = fallback
    return str(value or os.getenv(name, fallback) or "").strip()


def _resolve_ai_handler():
    configured = st.session_state.get("lesson_authoring_ai_handler")
    if callable(configured):
        return configured, "AI hệ thống"

    api_key = _secret("GEMINI_API_KEY")
    if not api_key:
        return None, "Chưa cấu hình Gemini"

    from portal_v2.ai.gemini_lesson_plan_service import (
        GeminiLessonPlanService,
    )

    service = GeminiLessonPlanService(
        api_key=api_key,
        model=_secret("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    )
    return service.revise, "Gemini Free Tier đã kết nối"


def _starter(context: dict[str, Any]) -> str:
    title = _value(context, "lesson_title", "Tên bài dạy")
    subject = _value(context, "subject_name", "Môn học")
    class_name = _value(context, "class_name", "Lớp")
    period = _value(context, "curriculum_period")
    teaching_date = _value(context, "teaching_date")
    return f"""KẾ HOẠCH BÀI DẠY

Môn học: {subject}
Lớp: {class_name}
Tên bài dạy: {title}
Tiết theo PPCT: {period}
Ngày thực hiện: {teaching_date}

I. MỤC TIÊU
1. Kiến thức
- Nêu rõ kiến thức trọng tâm học sinh cần đạt.

2. Năng lực
- Năng lực chung.
- Năng lực đặc thù môn học.

3. Phẩm chất
- Phẩm chất được hình thành trong bài học.

II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU
- Giáo viên:
- Học sinh:

III. TIẾN TRÌNH DẠY HỌC
1. Hoạt động mở đầu
a) Mục tiêu:
b) Nội dung:
c) Sản phẩm:
d) Tổ chức thực hiện:

2. Hoạt động hình thành kiến thức
a) Mục tiêu:
b) Nội dung:
c) Sản phẩm:
d) Tổ chức thực hiện:

3. Hoạt động luyện tập
a) Mục tiêu:
b) Nội dung:
c) Sản phẩm:
d) Tổ chức thực hiện:

4. Hoạt động vận dụng
a) Mục tiêu:
b) Nội dung:
c) Sản phẩm:
d) Tổ chức thực hiện:

IV. ĐIỀU CHỈNH SAU BÀI DẠY
"""


def _checks(text: str) -> tuple[tuple[str, bool], ...]:
    value = str(text or "").upper()
    return (
        ("Mục tiêu", "MỤC TIÊU" in value),
        ("Năng lực và phẩm chất", "NĂNG LỰC" in value and "PHẨM CHẤT" in value),
        ("Thiết bị và học liệu", "THIẾT BỊ" in value or "HỌC LIỆU" in value),
        ("Tiến trình dạy học", "TIẾN TRÌNH" in value or "HOẠT ĐỘNG" in value),
        ("Sản phẩm học tập", "SẢN PHẨM" in value),
        ("Điều chỉnh sau bài dạy", "ĐIỀU CHỈNH SAU" in value),
    )


def _remember(text: str) -> None:
    history = list(st.session_state.get(UNDO_KEY, ()))
    if not history or history[-1] != text:
        history.append(text)
    st.session_state[UNDO_KEY] = history[-12:]


def _set_document(text: str) -> None:
    current = str(st.session_state.get(DOCUMENT_KEY, ""))
    _remember(current)
    st.session_state[DOCUMENT_KEY] = str(text)


def _queue_document(text: str) -> None:
    """Queue a document update for the next run, before widget creation."""
    st.session_state[PENDING_DOCUMENT_KEY] = str(text)


def _normalize_document(text: str) -> str:
    lines = [line.rstrip() for line in str(text or "").replace("\r\n", "\n").split("\n")]
    result: list[str] = []
    blank = False
    for line in lines:
        if not line.strip():
            if not blank:
                result.append("")
            blank = True
        else:
            result.append(line)
            blank = False
    return "\n".join(result).strip()


def _catalog_identity(
    context: dict[str, Any],
    *,
    user_id: str,
    document: str,
) -> str:
    identity = (
        str(user_id or ""),
        str(context.get("subject_ref", "") or context.get("subject_name", "")),
        str(context.get("component_ref", "") or ""),
        str(context.get("class_id", "") or context.get("class_name", "")),
        str(context.get("lesson_id", "") or context.get("lesson_title", "")),
        str(context.get("curriculum_period", "") or ""),
        str(context.get("teaching_date", "") or ""),
    )
    if not any(identity[1:]):
        identity = identity + (sha256(document.encode("utf-8")).hexdigest(),)
    return sha256(repr(identity).encode("utf-8")).hexdigest()[:20]


def _save_to_management_catalog(
    document: str,
    context: dict[str, Any],
    *,
    user_id: str,
) -> str:
    """Insert or update one user-owned lesson in the session catalogue."""
    item_id = _catalog_identity(
        context,
        user_id=user_id,
        document=document,
    )
    working_docx_bytes = None
    try:
        from lesson_planning_v2.services.lesson_plan_workspace_v1_service import (
            LessonPlanFullDocumentDocxAdapter,
        )

        working_docx_bytes = (
            LessonPlanFullDocumentDocxAdapter().build_bytes(document)
        )
    except Exception:
        original_bytes = st.session_state.get(SOURCE_BYTES_KEY)
        if isinstance(original_bytes, (bytes, bytearray)):
            working_docx_bytes = bytes(original_bytes)

    item = {
        "item_id": item_id,
        "user_id": str(user_id or ""),
        "academic_year": str(context.get("academic_year", "") or ""),
        "week_number": int(context.get("week_number", 0) or 0),
        "subject_ref": str(context.get("subject_ref", "") or ""),
        "component_ref": str(context.get("component_ref", "") or ""),
        "subject_name": _value(context, "subject_name", "Chưa xác định"),
        "class_ref": str(
            context.get("class_id", "")
            or context.get("class_name", "")
            or ""
        ),
        "class_name": _value(context, "class_name", "Chưa xác định"),
        "lesson_id": str(context.get("lesson_id", "") or ""),
        "lesson_title": _value(context, "lesson_title", "Giáo án chưa đặt tên"),
        "curriculum_period": _value(context, "curriculum_period", "-"),
        "timetable_period": _value(context, "timetable_period", "-"),
        "teaching_date": _value(context, "teaching_date", "-"),
        # Preserve the complete canonical context beside the searchable
        # catalogue fields so reopening the draft cannot lose multi-class,
        # multi-date or week-scoped PPCT information.
        "linked_lesson_context": dict(context),
        "classes": tuple(context.get("classes", ()) or ()),
        "periods": tuple(context.get("periods", ()) or ()),
        "teaching_dates_by_class": tuple(
            context.get("teaching_dates_by_class", ()) or ()
        ),
        "timetable_periods_by_class": tuple(
            context.get("timetable_periods_by_class", ()) or ()
        ),
        "teaching_date_display": _value(
            context, "teaching_date_display", "-"
        ),
        "timetable_period_display": _value(
            context, "timetable_period_display", "-"
        ),
        "drafting_date": _value(
            context,
            "drafting_date",
            _value(context, "teaching_date", "-"),
        ),
        "document": str(document),
        "docx_bytes": working_docx_bytes,
        "source_bytes": st.session_state.get(SOURCE_BYTES_KEY),
        "source_name": str(
            st.session_state.get(SOURCE_NAME_KEY, "") or ""
        ),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    catalogue = list(
        st.session_state.get(MANAGEMENT_CATALOG_KEY, ()) or ()
    )
    catalogue = [
        existing
        for existing in catalogue
        if str(existing.get("item_id", "")) != item_id
    ]
    catalogue.append(item)
    st.session_state[MANAGEMENT_CATALOG_KEY] = catalogue[-100:]
    st.session_state["lesson_plan_management_selected_id"] = item_id
    _publish_standardization_transfer(item)
    return item_id


def _publish_standardization_transfer(item: dict[str, Any]) -> None:
    """Publish the canonical payload consumed by the standardization page."""
    transfer_key = (
        "lesson_authoring_ai_"
        + str(item.get("item_id", "lesson"))
        + "_standardization_transfer"
    )
    # Reinsert so this payload is the newest candidate in session order.
    st.session_state.pop(transfer_key, None)
    st.session_state[transfer_key] = {
        "source": "AI_DRAFT",
        "transfer_id": (
            str(item.get("item_id", ""))
            + ":"
            + str(item.get("updated_at", ""))
        ),
        "docx_bytes": item.get("docx_bytes"),
        "source_bytes": item.get("source_bytes"),
        "source_sha256": (
            sha256(bytes(item.get("source_bytes"))).hexdigest()
            if isinstance(item.get("source_bytes"), (bytes, bytearray))
            else ""
        ),
        "source_name": str(
            item.get("source_name", "")
            or (str(item.get("lesson_title", "giao-an-ai")) + ".docx")
        ),
        "teacher_user_id": str(item.get("user_id", "")),
        # STANDARDIZATION_TO_AI_ONE_WAY_V1
        # The AI may return the edited document, but schedule metadata must
        # never flow back and override standardization/LBG context.
        "full_document_text": str(item.get("document", "")),
    }


def _open_standardization(
    document: str,
    context: dict[str, Any],
    user_id: str,
) -> None:
    """Catalogue the lesson and navigate to the standardization workflow."""
    _save_to_management_catalog(
        document,
        dict(context or {}),
        user_id=user_id,
    )
    source_snapshot = dict(
        st.session_state.get(WORKING_CONTEXT_KEY, {}) or context or {}
    )
    st.session_state[WORKING_CONTEXT_KEY] = source_snapshot
    st.session_state[RESTORE_CONTEXT_KEY] = True
    st.session_state[NAVIGATION_NOTICE_KEY] = (
        "Đã tự lưu bài soạn và giữ nguyên thông tin liên kết khi chuyển sang Chuẩn hóa."
    )
    # ONE_WAY_LBG_DATA_FLOW_V1
    # The AI page may transfer its document to standardization, but it must
    # never write schedule metadata back into Lịch báo giảng state.  The
    # authoritative year/week continues to come from the active LBG view.
    st.session_state[
        "lesson_authoring_standardization_document"
    ] = document
    st.session_state[
        "lesson_authoring_tool_focus"
    ] = "STANDARDIZE"
    st.session_state[
        "portal_page"
    ] = "Chuẩn hóa giáo án"
    st.session_state[
        "portal_navigation"
    ] = "Chuẩn hóa giáo án"


def _schedule_context_selector(
    context: dict[str, Any],
    *,
    client=None,
    user_id: str = "",
) -> tuple[dict[str, Any], bool]:
    """Select an assigned subject, then one canonical schedule row.

    The subject/component menu is sourced from the teacher's ACTIVE teaching
    assignments.  Every dependent field is then copied from one schedule row
    so values from different lessons can never be mixed.
    """
    # STANDARDIZATION_TO_AI_ONE_WAY_V1
    # A context explicitly opened from standardization is already canonical.
    # Consume it exactly as transferred and do not let destination selectors
    # replace any field.
    if (
        context.get("context_origin") == "STANDARDIZATION"
        and context.get("context_read_only") is True
    ):
        received = dict(context)
        st.session_state[CONTEXT_KEY] = received
        return received, True

    view = st.session_state.get("weekly_schedule_portal_view")
    rows = tuple(getattr(view, "rows", ()) or ())
    academic_year = str(
        getattr(view, "academic_year", "")
        or context.get("academic_year", "")
        or ""
    ).strip()

    # The AI page can be opened directly, before a weekly schedule has been
    # loaded.  In that case resolve the year independently instead of making
    # assignment data depend on another page having been visited first.
    if not academic_year:
        for state_key in (
            "lbg_user_academic_year",
            "portal_academic_year",
            "system_weekly_academic_year",
            "teacher_data_academic_year",
            "weekly_schedule_academic_year",
        ):
            candidate = str(st.session_state.get(state_key, "") or "").strip()
            if candidate:
                academic_year = candidate
                break
    if not academic_year and client is not None:
        try:
            from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
                SupabaseAcademicYearConfigurationRepository,
            )

            current_year = SupabaseAcademicYearConfigurationRepository(
                client=client,
            ).get_current()
            academic_year = str(
                getattr(current_year, "academic_year", "") or ""
            ).strip()
        except Exception:
            pass
    if academic_year:
        context = dict(context)
        context["academic_year"] = academic_year

    assignment_pairs: list[tuple[str, str]] = []
    assignment_classes: dict[tuple[str, str], set[str]] = {}
    if client is not None and user_id and academic_year:
        try:
            from educational_planning_v2.adapters.supabase_teaching_assignment_repository import (
                SupabaseTeachingAssignmentRepository,
            )
            from educational_planning_v2.models.teaching_assignment import (
                TeachingAssignmentRole,
                TeachingAssignmentStatus,
            )

            assignments = SupabaseTeachingAssignmentRepository(
                client=client,
                user_id=user_id,
            ).list_assignments(
                owner_id=user_id,
                academic_year=academic_year,
                role=TeachingAssignmentRole.TEACHING,
                status=TeachingAssignmentStatus.ACTIVE,
            )
            for assignment in assignments:
                pair = (
                    str(assignment.subject_ref or "").strip(),
                    str(assignment.component_ref or "").strip(),
                )
                if not pair[0] or pair in assignment_pairs:
                    if pair[0]:
                        assignment_classes.setdefault(pair, set()).add(
                            str(assignment.class_id or "").strip()
                        )
                    continue
                assignment_pairs.append(pair)
                assignment_classes.setdefault(pair, set()).add(
                    str(assignment.class_id or "").strip()
                )
        except Exception as error:
            st.warning(
                "Chưa thể đọc Nhiệm vụ được phân công; "
                f"hệ thống tạm dùng dữ liệu Lịch báo giảng. ({error})"
            )

    # Safe fallback keeps the page usable when assignment storage is
    # temporarily unavailable, while still deriving options from teacher data.
    if not assignment_pairs:
        for row in rows:
            pair = (
                str(getattr(row, "subject_ref", "") or "").strip(),
                str(getattr(row, "component_ref", "") or "").strip(),
            )
            if pair[0] and pair not in assignment_pairs:
                assignment_pairs.append(pair)

    if not assignment_pairs:
        st.info(
            "Chưa có Nhiệm vụ được phân công hoặc Lịch báo giảng phù hợp. "
            "Hãy kiểm tra phân công chuyên môn của giáo viên."
        )
        return context, False

    def subject_label(pair: tuple[str, str]) -> str:
        subject_ref, component_ref = pair
        if client is not None:
            try:
                from portal_v2.ui.weekly_schedule_streamlit import (
                    _subject_display_name,
                )

                return _subject_display_name(
                    subject_ref=subject_ref,
                    component_ref=component_ref,
                    client=client,
                )
            except Exception:
                pass
        return component_ref or subject_ref

    current_pair = (
        str(context.get("subject_ref", "") or ""),
        str(context.get("component_ref", "") or ""),
    )
    default_subject_index = (
        assignment_pairs.index(current_pair)
        if current_pair in assignment_pairs
        else 0
    )
    selected_pair = st.selectbox(
        "Môn/phân môn",
        options=tuple(assignment_pairs),
        index=default_subject_index,
        format_func=subject_label,
        key="lesson_authoring_ai_assignment_subject",
        on_change=_notify_ai_context_change,
        args=("Môn/phân môn",),
        help=(
            "Danh sách lấy từ Nhiệm vụ được phân công đang hiệu lực "
            "của giáo viên."
        ),
    )
    allowed_classes = assignment_classes.get(selected_pair, set())
    filtered_rows = tuple(
        row
        for row in rows
        if (
            str(getattr(row, "subject_ref", "") or "").strip(),
            str(getattr(row, "component_ref", "") or "").strip(),
        ) == selected_pair
        and (
            not allowed_classes
            or str(getattr(row, "class_id", "") or "").strip()
            in allowed_classes
        )
    )
    if not filtered_rows:
        updated = dict(context)
        updated.update(
            subject_ref=selected_pair[0],
            component_ref=selected_pair[1],
            subject_name=subject_label(selected_pair),
        )
        st.session_state[CONTEXT_KEY] = updated
        st.info(
            "Môn/phân môn đã được chọn từ nhiệm vụ phân công nhưng chưa có "
            "bài tương ứng trong Lịch báo giảng hiện tại."
        )
        return updated, False

    def row_identity(row) -> tuple:
        return (
            getattr(row, "teaching_date", None),
            getattr(row, "timetable_period", None),
            str(getattr(row, "class_id", "") or ""),
            str(getattr(row, "lesson_title", "") or ""),
        )

    current_identity = (
        context.get("teaching_date"),
        context.get("timetable_period"),
        str(context.get("class_id", "") or ""),
        str(context.get("lesson_title", "") or ""),
    )
    default_index = 0
    for index, row in enumerate(filtered_rows):
        if row_identity(row) == current_identity:
            default_index = index
            break

    selected_index = st.selectbox(
        "Chọn bài từ Lịch báo giảng",
        options=tuple(range(len(filtered_rows))),
        index=default_index,
        format_func=lambda index: (
            f"{getattr(filtered_rows[index], 'teaching_date', ''):%d/%m/%Y} · "
            f"Tiết TKB {getattr(filtered_rows[index], 'timetable_period', '-')} · "
            f"{getattr(filtered_rows[index], 'class_id', '-')} · "
            f"{getattr(filtered_rows[index], 'lesson_title', 'Chưa có tên bài')}"
        ),
        key="lesson_authoring_ai_schedule_row",
        on_change=_notify_ai_context_change,
        args=("Bài từ Lịch báo giảng",),
    )
    row = filtered_rows[int(selected_index)]
    subject_ref = str(getattr(row, "subject_ref", "") or "")
    component_ref = str(getattr(row, "component_ref", "") or "")
    class_id = str(getattr(row, "class_id", "") or "")
    subject_name = component_ref or subject_ref
    class_name = class_id
    if client is not None:
        try:
            from portal_v2.ui.weekly_schedule_streamlit import (
                _class_display_name,
                _subject_display_name,
            )
            subject_name = _subject_display_name(
                subject_ref=subject_ref,
                component_ref=component_ref,
                client=client,
            )
            class_name = _class_display_name(
                class_id,
                client=client,
            )
        except Exception:
            pass
    linked = dict(context)
    linked.update(
        academic_year=str(getattr(view, "academic_year", "") or ""),
        week_number=int(getattr(view, "week_number", 0) or 0),
        subject_ref=subject_ref,
        component_ref=component_ref,
        subject_name=subject_name,
        class_id=class_id,
        class_name=class_name,
        lesson_id=str(getattr(row, "lesson_id", "") or ""),
        lesson_title=str(getattr(row, "lesson_title", "") or ""),
        curriculum_period=getattr(row, "curriculum_period", None),
        timetable_period=getattr(row, "timetable_period", None),
        teaching_date=getattr(row, "teaching_date", None),
        teaching_equipment=tuple(getattr(row, "teaching_equipment", ()) or ()),
    )
    st.session_state[CONTEXT_KEY] = linked
    st.session_state[AI_CONTEXT_DRAFT_KEY] = dict(linked)
    return linked, True


def _context_editor(
    context: dict[str, Any],
    *,
    linked: bool = False,
) -> dict[str, Any]:
    signature = sha256(
        repr(
            (
                context.get("teaching_date"),
                context.get("timetable_period"),
                context.get("class_id"),
                context.get("lesson_title"),
            )
        ).encode("utf-8")
    ).hexdigest()[:10]
    with st.expander("Thông tin bài dạy đã liên kết", expanded=True):
        row0 = st.columns(2)
        academic_year = row0[0].text_input(
            "Năm học", value=_value(context, "academic_year", ""),
            disabled=linked, key=f"ai_year_{signature}",
        )
        week_number = row0[1].text_input(
            "Tuần học", value=_value(context, "week_number", ""),
            disabled=linked, key=f"ai_week_{signature}",
        )
        row1 = st.columns(2)
        subject = row1[0].text_input(
            "Môn", value=_value(context, "subject_name", ""),
            disabled=linked, key=f"ai_subject_{signature}",
        )
        component = row1[1].text_input(
            "Phân môn", value=_value(context, "component_name", ""),
            disabled=linked, key=f"ai_component_{signature}",
        )
        row2 = st.columns(2)
        class_name = row2[0].text_input(
            "Lớp", value=_value(context, "class_name", ""),
            disabled=linked, key=f"ai_class_{signature}",
        )
        lesson_title = row2[1].text_input(
            "Tên bài dạy", value=_value(context, "lesson_title", ""),
            disabled=linked, key=f"ai_title_{signature}",
        )
        row3 = st.columns(2)
        curriculum_period = row3[0].text_input(
            "Tiết PPCT",
            value=(
                ", ".join(
                    str(value)
                    for value in tuple(context.get("periods", ()) or ())
                )
                or _value(context, "curriculum_period", "")
            ),
            disabled=linked, key=f"ai_ppct_{signature}",
        )
        timetable_period = row3[1].text_input(
            "Tiết TKB",
            value=_value(
                context,
                "timetable_period_display",
                _value(context, "timetable_period", ""),
            ),
            disabled=linked, key=f"ai_tkb_{signature}",
        )
        row4 = st.columns(2)
        if linked:
            row4[0].text_input(
                "Ngày dạy",
                value=_value(
                    context,
                    "teaching_date_display",
                    _value(context, "teaching_date", ""),
                ),
                disabled=True,
                key=f"ai_date_{signature}",
            )
            teaching_date = context.get("teaching_date")
        else:
            teaching_date = row4[0].date_input(
                "Ngày thực hiện",
                value=(
                    context.get("teaching_date")
                    if isinstance(context.get("teaching_date"), date)
                    else date.today()
                ),
                key=f"ai_date_{signature}",
            )
        equipment = row4[1].text_input(
            "Thiết bị dạy học",
            value=", ".join(
                str(value)
                for value in tuple(context.get("teaching_equipment", ()) or ())
            ),
            disabled=linked,
            key=f"ai_equipment_{signature}",
        )
        if linked:
            st.caption(
                "Các trường được nhận một chiều từ Chuẩn hóa giáo án/Lịch "
                "báo giảng và được khóa để không ghi ngược dữ liệu nguồn."
            )
    updated = dict(context)
    if not linked:
        updated.update(
            academic_year=academic_year,
            week_number=week_number,
            subject_name=subject,
            component_name=component,
            class_name=class_name,
            lesson_title=lesson_title,
            curriculum_period=curriculum_period,
            timetable_period=timetable_period,
            teaching_date=teaching_date,
            teaching_equipment=tuple(
                item.strip()
                for item in equipment.split(",")
                if item.strip()
            ),
        )
    st.session_state[CONTEXT_KEY] = updated
    return updated


def render_lesson_authoring_ai_page(*, client=None, user_id: str = "") -> None:
    """Render a square-edged, full-width lesson authoring workspace."""
    st.markdown(_PAGE_CSS, unsafe_allow_html=True)
    context = dict(
        st.session_state.get(CONTEXT_KEY)
        or st.session_state.get(WORKING_CONTEXT_KEY)
        or {}
    )
    navigation_notice = st.session_state.pop(NAVIGATION_NOTICE_KEY, "")
    if navigation_notice:
        st.toast(str(navigation_notice), icon="✅")
    autosave_notice = st.session_state.pop(AI_AUTOSAVE_NOTICE_KEY, "")
    if autosave_notice:
        st.toast(str(autosave_notice), icon="💾")
    pending_document = st.session_state.pop(PENDING_DOCUMENT_KEY, None)
    if pending_document is not None:
        _set_document(str(pending_document))
    st.session_state.setdefault(DOCUMENT_KEY, "")
    saved = st.session_state.get(SAVED_KEY) == st.session_state.get(DOCUMENT_KEY)
    status = "Đã lưu" if saved else "Đang chỉnh sửa"
    st.markdown(
        f"""<div class="mt-ai-page-header"><div><h1 class="mt-ai-page-title">SOẠN BÀI CÙNG AI</h1>
        <p class="mt-ai-page-subtitle">Nhập Word, biên tập toàn văn, kiểm tra và xuất giáo án trong một màn hình.</p>
        </div><div class="mt-ai-status">{escape(status)}</div></div>""",
        unsafe_allow_html=True,
    )
    context, linked = _schedule_context_selector(
        context,
        client=client,
        user_id=user_id,
    )
    context = _context_editor(
        context,
        linked=linked,
    )
    labels = (
        ("MÔN HỌC", _value(context, "subject_name")),
        ("PHÂN MÔN", _value(context, "component_name")),
        ("LỚP", _value(context, "class_name")),
        ("TÊN BÀI", _value(context, "lesson_title")),
        (
            "TIẾT TKB",
            _value(
                context,
                "timetable_period_display",
                _value(context, "timetable_period"),
            ),
        ),
        (
            "TIẾT PPCT",
            ", ".join(
                str(value)
                for value in tuple(context.get("periods", ()) or ())
            )
            or _value(context, "curriculum_period"),
        ),
        (
            "NGÀY DẠY",
            _value(
                context,
                "teaching_date_display",
                _value(context, "teaching_date"),
            ),
        ),
    )
    cards = "".join(
        f'<div class="mt-ai-context-item"><div class="mt-ai-context-label">{escape(label)}</div>'
        f'<div class="mt-ai-context-value">{escape(value)}</div></div>' for label, value in labels
    )
    st.markdown(f'<div class="mt-ai-context-grid">{cards}</div>', unsafe_allow_html=True)

    source_col, editor_col, assistant_col = st.columns([2.2, 7.2, 2.6], gap="medium")
    with source_col:
        st.markdown('<div class="mt-pane-label">NGUỒN GIÁO ÁN</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Tải giáo án Word", type=("docx",), key="lesson_authoring_ai_upload")
        if uploaded is not None:
            payload = uploaded.getvalue()
            digest = sha256(payload).hexdigest()
            if st.session_state.get(UPLOAD_HASH_KEY) != digest:
                try:
                    from lesson_planning_v2.services.lesson_plan_workspace_v1_service import LessonPlanDocxWholeDocumentImporter
                    imported = LessonPlanDocxWholeDocumentImporter().import_bytes(payload)
                    _set_document(imported)
                    st.session_state[SOURCE_BYTES_KEY] = payload
                    st.session_state[SOURCE_NAME_KEY] = uploaded.name
                    st.session_state[UPLOAD_HASH_KEY] = digest
                    st.session_state[AI_AUTOSAVE_NOTICE_KEY] = (
                        "Đã nhập và tự lưu giáo án Word vào phiên soạn bài."
                    )
                    st.rerun()
                except Exception as error:
                    st.error("Không thể đọc giáo án Word: " + str(error))
        if st.button("Tạo khung giáo án", use_container_width=True):
            _set_document(_starter(context))
            st.session_state[AI_AUTOSAVE_NOTICE_KEY] = (
                "Đã tạo và tự lưu khung giáo án."
            )
            st.rerun()
        history = list(st.session_state.get(UNDO_KEY, ()))
        if st.button("Hoàn tác", use_container_width=True, disabled=not history):
            st.session_state[DOCUMENT_KEY] = history.pop()
            st.session_state[UNDO_KEY] = history
            st.session_state[AI_AUTOSAVE_NOTICE_KEY] = (
                "Đã hoàn tác và lưu lại nội dung hiện tại."
            )
            st.rerun()
        if st.button("Làm sạch trình bày", use_container_width=True):
            _set_document(_normalize_document(st.session_state.get(DOCUMENT_KEY, "")))
            st.session_state[AI_AUTOSAVE_NOTICE_KEY] = (
                "Đã làm sạch trình bày và tự lưu nội dung."
            )
            st.rerun()
        if st.button("Lưu bản nháp", type="primary", use_container_width=True):
            st.session_state[SAVED_KEY] = st.session_state.get(DOCUMENT_KEY, "")
            st.success("Đã lưu bản nháp trong phiên làm việc.")
        st.markdown('<div class="mt-ai-page-note">Tệp Word gốc được giữ riêng. Nội dung nhập vào trình soạn là một bản làm việc.</div>', unsafe_allow_html=True)

    with editor_col:
        st.markdown('<div class="mt-ai-document-pane-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="mt-pane-label">CỬA SỔ CHỈNH SỬA TOÀN VĂN</div>', unsafe_allow_html=True)
        st.text_area(
            "Nội dung giáo án", key=DOCUMENT_KEY, height=790, label_visibility="collapsed",
            placeholder="Tải giáo án Word hoặc tạo khung mới để bắt đầu...",
            on_change=_autosave_ai_document,
        )

    with assistant_col:
        st.markdown('<div class="mt-pane-label">TRỢ LÝ SOẠN BÀI</div>', unsafe_allow_html=True)
        handler, ai_status = _resolve_ai_handler()
        if callable(handler):
            st.success(ai_status)
            st.caption(
                "Không nhập dữ liệu cá nhân nhạy cảm của học sinh. "
                "Gemini Free Tier có thể dùng nội dung để cải thiện sản phẩm."
            )
        else:
            st.warning(ai_status)
        quick_action = st.selectbox(
            "Công cụ nhanh",
            ("Chọn tác vụ", "Bổ sung hoạt động mở đầu", "Bổ sung câu hỏi phân hóa", "Bổ sung phiếu đánh giá", "Bổ sung điều chỉnh sau bài dạy"),
        )
        if st.button("Áp dụng công cụ", use_container_width=True, disabled=quick_action == "Chọn tác vụ"):
            additions = {
                "Bổ sung hoạt động mở đầu": "\n\nHOẠT ĐỘNG MỞ ĐẦU BỔ SUNG\n- Mục tiêu:\n- Tình huống thực tiễn:\n- Nhiệm vụ học tập:\n- Sản phẩm:\n- Tổ chức thực hiện:",
                "Bổ sung câu hỏi phân hóa": "\n\nCÂU HỎI PHÂN HÓA\n- Mức nhận biết:\n- Mức thông hiểu:\n- Mức vận dụng:\n- Hỗ trợ học sinh chưa đạt:\n- Mở rộng cho học sinh khá, giỏi:",
                "Bổ sung phiếu đánh giá": "\n\nPHIẾU ĐÁNH GIÁ\n- Tiêu chí 1:\n- Tiêu chí 2:\n- Minh chứng học tập:\n- Mức độ hoàn thành:",
                "Bổ sung điều chỉnh sau bài dạy": "\n\nIV. ĐIỀU CHỈNH SAU BÀI DẠY\n- Nội dung phù hợp:\n- Khó khăn của học sinh:\n- Điều chỉnh cho lần dạy tiếp theo:",
            }
            _queue_document(str(st.session_state.get(DOCUMENT_KEY, "")) + additions[quick_action])
            st.session_state[AI_AUTOSAVE_NOTICE_KEY] = (
                "Đã áp dụng công cụ và tự lưu thay đổi."
            )
            st.rerun()
        request = st.text_area("Yêu cầu AI", height=180, placeholder="Ví dụ: Viết lại hoạt động luyện tập theo hướng phân hóa...")
        if st.button("Gửi yêu cầu cho AI", type="primary", use_container_width=True, disabled=not request.strip()):
            if callable(handler):
                try:
                    with st.spinner("Gemini đang biên tập giáo án..."):
                        revised = handler(request=request, document=st.session_state.get(DOCUMENT_KEY, ""), context=context)
                    if str(revised or "").strip():
                        _queue_document(str(revised))
                        st.session_state[AI_AUTOSAVE_NOTICE_KEY] = (
                            "AI đã cập nhật và hệ thống đã tự lưu bài soạn."
                        )
                        st.rerun()
                except Exception as error:
                    st.error("AI chưa xử lý được yêu cầu: " + str(error))
            else:
                st.warning("Giao diện AI đã sẵn sàng; cần cấu hình dịch vụ AI của hệ thống để sinh nội dung.")
        checks = _checks(st.session_state.get(DOCUMENT_KEY, ""))
        passed = sum(1 for _, ok in checks if ok)
        st.metric("Mức độ đầy đủ", f"{passed}/{len(checks)}")
        for label, ok in checks:
            st.caption(("✅ " if ok else "⬜ ") + label)

    document = str(st.session_state.get(DOCUMENT_KEY, ""))
    action_cols = st.columns([1, 1, 1, 1])
    if document.strip():
        try:
            from lesson_planning_v2.services.lesson_plan_workspace_v1_service import LessonPlanFullDocumentDocxAdapter
            output = LessonPlanFullDocumentDocxAdapter().build_bytes(document)
            action_cols[0].download_button(
                "Tải giáo án Word", data=output,
                file_name=(_value(context, "lesson_title", "giao-an") + ".docx"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as error:
            action_cols[0].error(str(error))
    if action_cols[1].button("Giữ bản Word gốc", use_container_width=True, disabled=not st.session_state.get(SOURCE_BYTES_KEY)):
        st.info("Bản Word gốc vẫn được bảo toàn trong phiên làm việc.")
    action_cols[2].button(
        "Chuyển sang chuẩn hóa",
        use_container_width=True,
        disabled=not document.strip(),
        on_click=_open_standardization,
        args=(document, context, user_id),
    )
    action_cols[3].caption(f"{len(document):,} ký tự · người dùng {user_id[:8] or '-'}")
