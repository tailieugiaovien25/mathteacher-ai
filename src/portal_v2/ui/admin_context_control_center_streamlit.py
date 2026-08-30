from __future__ import annotations

from typing import Any

from portal_v2.context.ownership import build_default_context_ownership_registry
from portal_v2.context.registry import build_default_context_registry

_FIELD_LABELS = {"user_id":"Người dùng","teacher_id":"Giáo viên","academic_year":"Năm học","week_number":"Tuần học","subject_ref":"Môn học","component_ref":"Phân môn","grade":"Khối lớp","class_id":"Lớp","timetable_slot_id":"Tiết TKB","teaching_date":"Ngày dạy","timetable_period":"Tiết theo TKB","curriculum_period":"Tiết PPCT","lesson_id":"Bài học","source_page":"Trang phát sinh","source_control":"Điều khiển phát sinh","context_version":"Phiên bản ngữ cảnh"}
_KIND_LABELS = {"GLOBAL":"Toàn hệ thống","DERIVED":"Dữ liệu suy ra","LOCAL":"Cục bộ giao diện"}
_AUTHORITY_LABELS = {"IDENTITY":"Danh tính người dùng","TEACHING_ASSIGNMENT":"Phân công giảng dạy","ACADEMIC_CALENDAR":"Lịch năm học","ACTIVE_TEACHER_TIMETABLE":"Thời khóa biểu đang hiệu lực","PPCT_CURRICULUM":"PPCT / Chương trình","UI":"Giao diện người dùng","SYSTEM_CONTEXT":"Ngữ cảnh hệ thống"}
_STATUS_LABELS = {"OK":"Đồng bộ","WARNING":"Cảnh báo","ERROR":"Lỗi","STALE":"Dữ liệu cũ","CONFLICT":"Xung đột"}
_COLUMN_LABELS = {"canonical_field":"Trường ngữ cảnh","current_value":"Giá trị hiện tại","kind":"Loại ngữ cảnh","authority":"Nguồn dữ liệu chuẩn","state_keys":"Khóa trạng thái liên quan","observed_keys":"Khóa đang có dữ liệu","depends_on":"Phụ thuộc vào","invalidates":"Làm mới khi thay đổi","status":"Trạng thái đồng bộ"}
def _vi_field_list(value):
    if not value or value == "—": return "—"
    return ", ".join(_FIELD_LABELS.get(x.strip(), x.strip()) for x in value.split(","))
def _to_vietnamese_row(row):
    return {_COLUMN_LABELS["canonical_field"]:_FIELD_LABELS.get(row["canonical_field"],row["canonical_field"]),_COLUMN_LABELS["current_value"]:row["current_value"],_COLUMN_LABELS["kind"]:_KIND_LABELS.get(row["kind"],row["kind"]),_COLUMN_LABELS["authority"]:_AUTHORITY_LABELS.get(row["authority"],row["authority"]),_COLUMN_LABELS["state_keys"]:row["state_keys"],_COLUMN_LABELS["observed_keys"]:row["observed_keys"],_COLUMN_LABELS["depends_on"]:_vi_field_list(row["depends_on"]),_COLUMN_LABELS["invalidates"]:_vi_field_list(row["invalidates"]),_COLUMN_LABELS["status"]:_STATUS_LABELS.get(row["status"],row["status"])}


def _display_value(value: Any) -> str:
    if value is None:
        return "—"
    return str(value)


def build_admin_context_control_rows(*, session_state) -> tuple[dict[str, Any], ...]:
    registry = build_default_context_registry()
    ownership = build_default_context_ownership_registry()
    rows = []
    for spec in registry.all():
        aliases = ownership.aliases_for(spec.name)
        values = []
        observed_keys = []
        for item in aliases:
            if item.state_key in session_state:
                value = session_state.get(item.state_key)
                values.append(value)
                observed_keys.append(item.state_key)

        distinct = []
        for value in values:
            if value not in distinct:
                distinct.append(value)

        if len(distinct) > 1:
            status = "CONFLICT"
        elif aliases and not values:
            status = "STALE"
        elif not aliases:
            status = "WARNING"
        else:
            status = "OK"

        rows.append({
            "canonical_field": spec.name,
            "current_value": _display_value(distinct[0] if len(distinct) == 1 else None),
            "kind": spec.kind.value,
            "authority": spec.authority,
            "state_keys": ", ".join(item.state_key for item in aliases) or "—",
            "observed_keys": ", ".join(observed_keys) or "—",
            "depends_on": ", ".join(spec.depends_on) or "—",
            "invalidates": ", ".join(spec.invalidates) or "—",
            "status": status,
        })
    return tuple(rows)


def render_admin_context_control_center(st, *, authorization=None, client=None) -> None:
    del authorization, client
    st.title("Dữ liệu & Đồng bộ ngữ cảnh hệ thống")
    st.caption(
        "Giám sát SystemContext và Context Registry theo người dùng/phiên. "
        "V57-F2A chỉ đọc, không thay đổi dữ liệu và không tạo authority mới."
    )

    rows = build_admin_context_control_rows(session_state=st.session_state)
    counts = {name: 0 for name in ("OK", "WARNING", "ERROR", "STALE", "CONFLICT")}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trường canonical", len(rows))
    c2.metric("Đồng bộ", counts["OK"])
    c3.metric("Cần kiểm tra", counts["WARNING"] + counts["STALE"])
    c4.metric("Xung đột", counts["CONFLICT"])

    status_options = ("OK", "WARNING", "ERROR", "STALE", "CONFLICT")
    selected_status_labels = st.multiselect(
        "Trạng thái",
        tuple(_STATUS_LABELS[item] for item in status_options),
        default=tuple(_STATUS_LABELS[item] for item in status_options),
        key="admin_context_monitor_status_filter_vi",
    )
    selected_statuses = {code for code, label in _STATUS_LABELS.items() if label in selected_status_labels}
    visible = [_to_vietnamese_row(row) for row in rows if row["status"] in selected_statuses]
    st.dataframe(visible, use_container_width=True, hide_index=True)

    with st.expander("Quy tắc đồng bộ", expanded=False):
        st.markdown(
            "Widget → ContextChange → ContextSynchronizationService → SystemContext.  "
            "ADMIN chỉ là bề mặt giám sát/điều khiển. Authority vẫn theo "
            "Identity → Teaching Assignment → Academic Calendar → ACTIVE TKB → PPCT → LBG."
        )
