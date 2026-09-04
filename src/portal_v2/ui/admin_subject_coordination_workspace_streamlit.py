"""G1B_P1A_UNIFIED_ADMIN_SUBJECT_COMPONENT_READ_ONLY."""
from __future__ import annotations
from typing import Any
import streamlit as st


def _text(value: Any) -> str:
    return str(value or "").strip()


def _attr(item: Any, *names: str) -> str:
    for name in names:
        value = item.get(name) if isinstance(item, dict) else getattr(item, name, None)
        value = _text(value)
        if value:
            return value
    return ""


def _catalog(client: Any):
    candidates = (
        ("educational_planning_v2.adapters.supabase_subject_catalog_repository", "SupabaseSubjectCatalogRepository"),
        ("lesson_planning_v2.adapters.supabase_subject_catalog_repository", "SupabaseSubjectCatalogRepository"),
    )
    last = None
    for module_name, class_name in candidates:
        try:
            module = __import__(module_name, fromlist=[class_name])
            repo = getattr(module, class_name)(client=client)
            subjects = list(repo.list_subjects())
            try:
                components = list(repo.list_components())
            except TypeError:
                components = []
                for subject in subjects:
                    sid = _attr(subject, "subject_id", "id", "subject_ref")
                    if sid:
                        components.extend(list(repo.list_components(subject_id=sid)))
            return subjects, components
        except Exception as exc:
            last = exc
    raise RuntimeError("CANONICAL_SUBJECT_CATALOG_UNAVAILABLE") from last


def _lesson_plan_effective(client: Any, subject_ref: str, component_ref: str):
    try:
        from lesson_planning_v2.adapters.supabase_lesson_plan_configuration_repository import SupabaseLessonPlanConfigurationRepository
        from lesson_planning_v2.services.lesson_plan_configuration_service import LessonPlanConfigurationService
        repo = SupabaseLessonPlanConfigurationRepository(client)
        service = LessonPlanConfigurationService(repository=repo)
        return "OK", service.resolve(subject_ref=subject_ref, component_ref=component_ref, fallback_payload={})
    except Exception as exc:
        return "Chưa xác định", f"{type(exc).__name__}: {exc}"


def _grouping_effective(client: Any, subject_ref: str, component_ref: str):
    try:
        from lesson_planning_v2.adapters.supabase_lesson_plan_grouping_policy_repository import SupabaseLessonPlanGroupingPolicyRepository
        from lesson_planning_v2.services.lesson_plan_grouping_service import LessonPlanGroupingPolicyResolver
        configs = SupabaseLessonPlanGroupingPolicyRepository(client=client).list_configs()
        active = [c for c in configs if bool(getattr(c, "active", False))]
        resolver = LessonPlanGroupingPolicyResolver(active)
        return "OK", resolver.resolve(subject_ref=subject_ref, component_ref=component_ref)
    except Exception as exc:
        return "Chưa xác định", f"{type(exc).__name__}: {exc}"


def _display_name(item: Any, *, fallback: str) -> str:
    return _attr(item, "subject_name", "component_name", "name", "display_name") or fallback


def _enum_text(value: Any) -> str:
    raw = getattr(value, "value", value)
    return _text(raw)


def _snapshot_field(snapshot: Any, name: str) -> str:
    if snapshot is None:
        return ""
    return _text(getattr(snapshot, name, ""))


# G1B_P1B_R2A_R4_EXACT_EFFECTIVE_DETAILS
def _render_lesson_plan_configuration_details(st, payload: Any) -> None:
    normalized = dict(payload) if isinstance(payload, dict) else {}
    template_profile = normalized.get("template_profile")
    template_profile = template_profile if isinstance(template_profile, dict) else {}
    layout = template_profile.get("layout")
    layout = layout if isinstance(layout, dict) else {}
    date_policy = normalized.get("date_policy")
    date_policy = date_policy if isinstance(date_policy, dict) else {}
    approval_policy = normalized.get("approval_policy")
    approval_policy = approval_policy if isinstance(approval_policy, dict) else {}
    document_repository = normalized.get("document_repository")
    document_repository = document_repository if isinstance(document_repository, dict) else {}

    st.markdown("##### Chi tiết cấu hình giáo án hiệu lực")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Mẫu và định dạng trình bày", "Ngày soạn và ngày duyệt", "Phê duyệt", "Kho giáo án"]
    )
    with tab1:
        st.write({
            "Tên mẫu": template_profile.get("profile_name"),
            "Phông chữ": layout.get("font_name"),
            "Cỡ chữ nội dung": layout.get("body_font_size_pt"),
            "Giãn dòng": layout.get("line_spacing"),
            "Lề trái (cm)": layout.get("margin_left_cm"),
            "Lề phải (cm)": layout.get("margin_right_cm"),
            "Lề trên (cm)": layout.get("margin_top_cm"),
            "Lề dưới (cm)": layout.get("margin_bottom_cm"),
        })
    with tab2:
        st.write({
            "Soạn trước thứ Hai": date_policy.get("drafting_before_monday_enabled"),
            "Số ngày soạn trước": date_policy.get("drafting_before_monday_days"),
            "Duyệt trước thứ Hai": date_policy.get("approval_before_monday_enabled"),
            "Số ngày duyệt trước": date_policy.get("approval_before_monday_days"),
        })
    with tab3:
        st.write({
            "Nhãn phê duyệt": approval_policy.get("approval_label"),
            "Căn lề": approval_policy.get("alignment"),
            "Độ lệch ngày duyệt": approval_policy.get("approval_offset_days"),
        })
    with tab4:
        folder_id = _text(document_repository.get("google_drive_lesson_plan_folder_id"))
        st.write({"Google Drive lesson-plan folder ID": folder_id or None})
        st.caption(
            "Chỉ hiển thị folder ID thuộc cấu hình giáo án hiệu lực. "
            "Kho lưu trữ / Drive / Library tổng quát vẫn UNKNOWN."
        )


def _render_lesson_plan_effective(st, *, status: str, value: Any) -> None:
    st.markdown("#### Chuẩn hóa giáo án / cấu hình giáo án")
    if status != "OK":
        st.warning("Chưa xác định")
        st.caption(_text(value))
        return
    source = _text(getattr(value, "source", "")) or "Chưa xác định"
    snapshot = getattr(value, "snapshot", None)
    payload = getattr(value, "configuration_payload", {}) or {}
    locked_paths = tuple(getattr(value, "locked_paths", ()) or ())
    conflicts = tuple(getattr(value, "conflicts", ()) or ())

    if locked_paths:
        st.info(
            "Các giá trị dưới đây được kế thừa từ Cấu hình giáo án toàn hệ thống "
            "và chỉ được xem tại cấu hình theo môn."
        )
        with st.expander("Giá trị toàn hệ thống đang khóa", expanded=False):
            st.write([{"Trường chỉ đọc": path} for path in locked_paths])
    if conflicts:
        st.warning(
            "Cấu hình môn có giá trị mâu thuẫn nhưng không được áp dụng: "
            + ", ".join(conflicts)
        )
    _render_lesson_plan_configuration_details(st, payload)
    if snapshot is None:
        st.info("CURRENT DEFAULT")
        st.caption("Chưa có cấu hình ADMIN ACTIVE/PUBLISHED phù hợp. Runtime tiếp tục dùng mặc định hiện hành.")
        st.write({"Nguồn": source, "Phạm vi": "Mặc định runtime hiện hành"})
        return
    st.success("ADMIN ACTIVE / PUBLISHED")
    st.write({
        "Nguồn": source,
        "Hồ sơ": _snapshot_field(snapshot, "profile_name"),
        "Mã hồ sơ": _snapshot_field(snapshot, "profile_code"),
        "Môn": _snapshot_field(snapshot, "subject_ref") or "GLOBAL",
        "Phân môn": _snapshot_field(snapshot, "component_ref") or "Mặc định môn / GLOBAL",
        "Phiên bản": _snapshot_field(snapshot, "version_number"),
        "Configuration version ID": _snapshot_field(snapshot, "configuration_version_id"),
    })
    if isinstance(payload, dict) and payload:
        with st.expander("Thông số cấu hình hiệu lực", expanded=True):
            st.json(dict(payload))
    else:
        st.caption("Configuration payload hiện tại rỗng.")

    # G1B_P1B_R2A_EFFECTIVE_LESSON_PLAN_DETAILS_CALL
    _g1b_p1b_r2a_render_effective_lesson_plan_details(st, configuration_payload)

# G1B_P1B_R2A_EFFECTIVE_LESSON_PLAN_DETAILS
def _g1b_p1b_r2a_render_effective_lesson_plan_details(st, payload) -> None:
    normalized = dict(payload or {})
    template_profile = normalized.get("template_profile")
    template_profile = template_profile if isinstance(template_profile, dict) else {}
    layout = template_profile.get("layout")
    layout = layout if isinstance(layout, dict) else {}
    date_policy = normalized.get("date_policy")
    date_policy = date_policy if isinstance(date_policy, dict) else {}
    approval_policy = normalized.get("approval_policy")
    approval_policy = approval_policy if isinstance(approval_policy, dict) else {}
    document_repository = normalized.get("document_repository")
    document_repository = document_repository if isinstance(document_repository, dict) else {}

    st.markdown("#### Chi tiet cau hinh giao an hieu luc")
    st.caption("READ ONLY tu resolved configuration hien tai; khong ghi CSDL.")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Mau & trinh bay", "Ngay soan / ngay duyet", "Phe duyet", "Kho giao an"]
    )
    with tab1:
        st.write({
            "profile_name": template_profile.get("profile_name"),
            "font_name": layout.get("font_name"),
            "body_font_size_pt": layout.get("body_font_size_pt"),
            "line_spacing": layout.get("line_spacing"),
            "margin_left_cm": layout.get("margin_left_cm"),
            "margin_right_cm": layout.get("margin_right_cm"),
            "margin_top_cm": layout.get("margin_top_cm"),
            "margin_bottom_cm": layout.get("margin_bottom_cm"),
        })
    with tab2:
        st.write({
            "drafting_before_monday_enabled": date_policy.get("drafting_before_monday_enabled"),
            "drafting_before_monday_days": date_policy.get("drafting_before_monday_days"),
            "approval_before_monday_enabled": date_policy.get("approval_before_monday_enabled"),
            "approval_before_monday_days": date_policy.get("approval_before_monday_days"),
        })
    with tab3:
        st.write({
            "approval_label": approval_policy.get("approval_label"),
            "alignment": approval_policy.get("alignment"),
            "approval_offset_days": approval_policy.get("approval_offset_days"),
        })
    with tab4:
        folder_id = str(document_repository.get("google_drive_lesson_plan_folder_id") or "").strip()
        st.write({"google_drive_lesson_plan_folder_id": folder_id or None})
        st.info("Drive / Library / Storage tong quat van UNKNOWN; day chi la kho giao an trong lesson-plan configuration.")



# G1B_P1B_R3A_STANDARDIZER_SUBJECT_CAPABILITY_DASHBOARD
# G1B_P1B_R3B_VIETNAMESE_PRESENTATION_LAYER
def _g1b_p1b_r3a_standardizer_capabilities(
    *,
    subject_ref: str,
    component_ref: str,
    status: str,
    value: Any,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(capability: str, state: str, evidence: str, verification: str = "Đã xác nhận ở mã nguồn") -> None:
        rows.append({
            "Tính năng": capability,
            "Trạng thái": state,
            "Căn cứ / nguồn cấu hình": evidence,
            "Mức xác nhận": verification,
        })

    if status != "OK":
        add("Cấu hình Chuẩn hóa giáo án đang áp dụng", "Chưa xác định", _text(value) or "Không đọc được cấu hình hiệu lực của Môn/Phân môn đang chọn.", "Chưa xác định")
        payload = {}
    else:
        snapshot = getattr(value, "snapshot", None)
        payload = getattr(value, "configuration_payload", {}) or {}
        if snapshot is None:
            add("Cấu hình Chuẩn hóa giáo án đang áp dụng", "Theo cấu hình Môn/Phân môn", "Cấu hình mặc định hiện hành cho Môn/Phân môn đang chọn.")
        else:
            scope_subject = _snapshot_field(snapshot, "subject_ref") or "GLOBAL"
            scope_component = _snapshot_field(snapshot, "component_ref") or ""
            evidence = "Cấu hình ADMIN đang hoạt động: " + (_snapshot_field(snapshot, "profile_name") or "Hồ sơ ADMIN") + " | " + str(scope_subject)
            if scope_component:
                evidence += " / " + str(scope_component)
            add("Cấu hình Chuẩn hóa giáo án đang áp dụng", "Theo cấu hình Môn/Phân môn", evidence)

    normalized = dict(payload) if isinstance(payload, dict) else {}
    template_profile = normalized.get("template_profile")
    template_profile = template_profile if isinstance(template_profile, dict) else {}
    date_policy = normalized.get("date_policy")
    date_policy = date_policy if isinstance(date_policy, dict) else {}
    approval_policy = normalized.get("approval_policy")
    approval_policy = approval_policy if isinstance(approval_policy, dict) else {}
    document_repository = normalized.get("document_repository")
    document_repository = document_repository if isinstance(document_repository, dict) else {}

    add("Nhận diện thông tin giáo án theo môn", "Hoạt động một phần", "Có cơ chế nhận diện và cập nhật thông tin giáo án dùng chung; mức bao phủ riêng cho từng môn chưa được xác nhận đầy đủ.", "Hoạt động một phần")

    date_keys = ("drafting_before_monday_enabled", "drafting_before_monday_days", "approval_before_monday_enabled", "approval_before_monday_days")
    if any(key in date_policy for key in date_keys):
        add("Ngày soạn và ngày duyệt", "Theo cấu hình Môn/Phân môn", "Cấu hình ngày soạn/ngày duyệt đã có trong cấu hình hiệu lực của Môn/Phân môn đang chọn.")
    else:
        add("Ngày soạn và ngày duyệt", "Chưa xác định", "Cấu hình hiệu lực hiện chưa có thiết lập cụ thể cho ngày soạn/ngày duyệt.", "Chưa xác định")

    if approval_policy:
        add("Khối phê duyệt của Tổ chuyên môn", "Theo cấu hình Môn/Phân môn", "Thiết lập khối phê duyệt đã có trong cấu hình hiệu lực của Môn/Phân môn đang chọn.")
    else:
        add("Khối phê duyệt của Tổ chuyên môn", "Chưa xác định", "Cấu hình hiệu lực hiện chưa có thiết lập cụ thể cho khối phê duyệt.", "Chưa xác định")

    if template_profile:
        add("Mẫu và định dạng trình bày", "Theo cấu hình Môn/Phân môn", "Mẫu và định dạng trình bày đã có trong cấu hình hiệu lực của Môn/Phân môn đang chọn.")
    else:
        add("Mẫu và định dạng trình bày", "Chưa xác định", "Cấu hình hiệu lực hiện chưa có mẫu và định dạng trình bày cụ thể.", "Chưa xác định")

    folder_id = _text(document_repository.get("google_drive_lesson_plan_folder_id"))
    if folder_id:
        add("Thư mục lưu giáo án", "Theo cấu hình Môn/Phân môn", "Đã xác định thư mục lưu giáo án trong cấu hình hiệu lực.")
    else:
        add("Thư mục lưu giáo án", "Chưa xác định", "Chưa xác định thư mục lưu giáo án trong cấu hình hiệu lực; không suy diễn trạng thái kho Drive/Library tổng quát.", "Chưa xác định")

    add("Giữ nguyên bảng biểu và hình ảnh trong giáo án Word", "Chức năng lõi dùng chung", "Chức năng lõi dùng chung của bộ chuẩn hóa; không phải tùy chọn bật/tắt riêng theo từng môn.")
    add("Bảo toàn công thức Toán học (MathType/OLE)", "Chức năng lõi dùng chung", "Chức năng lõi dùng chung; không tạo thành cấu hình riêng cho từng môn.")
    add("Gộp nhiều giáo án đã chuẩn hóa", "Chức năng lõi dùng chung", "Chức năng gộp giáo án là năng lực dùng chung; không coi là cấu hình riêng của từng môn.")
    add("Xác nhận hoạt động thực tế theo môn", "Chưa xác định", "Bảng điều khiển không tự coi chức năng là hoạt động thực tế chỉ vì mã nguồn tồn tại; chỉ xác nhận sau khi có kiểm thử thực tế được ghi nhận.", "Chưa xác định")
    return rows


def _g1b_p1b_r3a_render_standardizer_capability_dashboard(
    st,
    *,
    subject_ref: str,
    component_ref: str,
    status: str,
    value: Any,
) -> None:
    st.subheader("Các tính năng kỹ thuật của công cụ Chuẩn hóa giáo án")
    st.caption("CHỈ XEM · Hiển thị theo Môn/Phân môn đang chọn. Chức năng lõi dùng chung chỉ là chỉ báo kỹ thuật, không phải nút điều khiển riêng theo môn.")
    rows = _g1b_p1b_r3a_standardizer_capabilities(subject_ref=subject_ref, component_ref=component_ref, status=status, value=value)
    # G1B_P1B_R3D_CAPABILITY_TABLE_LAYOUT
    st.dataframe(
        rows,
        hide_index=True,
        use_container_width=True,
        height=388,
        column_config={
            "Tính năng": st.column_config.TextColumn(
                "Tính năng",
                width="large",
                help="Tên chức năng hoặc năng lực kỹ thuật của công cụ Chuẩn hóa giáo án.",
            ),
            "Trạng thái": st.column_config.TextColumn(
                "Trạng thái",
                width="medium",
                help="Mức áp dụng hiện tại đối với Môn/Phân môn đang chọn.",
            ),
            "Căn cứ / nguồn cấu hình": st.column_config.TextColumn(
                "Căn cứ / nguồn cấu hình",
                width="large",
                help="Giải thích nguồn cấu hình hoặc căn cứ kỹ thuật của trạng thái.",
            ),
            "Mức xác nhận": st.column_config.TextColumn(
                "Mức xác nhận",
                width="medium",
                help="Mức độ đã được kiểm chứng của tính năng.",
            ),
        },
    )
    st.caption("Không tự xác nhận chức năng đã hoạt động thực tế. Trạng thái Chưa xác định/Hoạt động một phần được giữ nguyên cho tới khi có bằng chứng kiểm thử tương ứng.")


def _render_grouping_effective(st, *, status: str, value: Any) -> None:
    st.markdown("#### Chính sách nhóm giáo án")
    if status != "OK":
        st.warning("Chưa xác định")
        st.caption(_text(value))
        return
    mode = _enum_text(value)
    st.success("ACTIVE RESOLVED")
    st.write({
        "Chế độ nhóm hiệu lực": mode or "Chưa xác định",
        "Thứ tự resolve": "Phân môn -> mặc định Môn -> mặc định hệ thống",
    })


# G1B_P1B_R1_UNIFIED_EFFECTIVE_CONFIGURATION_VIEW
def render_admin_subject_coordination_workspace(*, client: Any) -> None:
    st.title("Trung tâm điều phối theo Môn / Phân môn")
    st.caption("P1B - Cấu hình hiệu lực READ ONLY. Không ghi dữ liệu và không thay đổi runtime.")
    try:
        subjects, components = _catalog(client)
    except Exception as exc:
        st.error("Không đọc được danh mục Môn canonical.")
        st.code(f"{type(exc).__name__}: {exc}")
        return
    subject_by = {_attr(x, "subject_id", "id", "subject_ref"): x for x in subjects if _attr(x, "subject_id", "id", "subject_ref")}
    if not subject_by:
        st.warning("UNKNOWN: Không có Môn canonical khả dụng.")
        return
    sid = st.selectbox("Môn", tuple(subject_by), format_func=lambda x: f"{_display_name(subject_by[x], fallback=x)} ({x})", key="g1b_p1a_subject_ref")
    component_by = {_attr(x, "component_id", "id", "component_ref"): x for x in components if _attr(x, "component_id", "id", "component_ref") and _attr(x, "subject_id", "subject_ref") == sid}
    none_label = "-- Mặc định của môn --"
    selected = st.selectbox("Phân môn", (none_label,) + tuple(component_by), format_func=lambda x: none_label if x == none_label else f"{_display_name(component_by[x], fallback=x)} ({x})", key="g1b_p1a_component_ref")
    cid = "" if selected == none_label else selected
    if cid and _attr(component_by[cid], "subject_id", "subject_ref") != sid:
        st.error("BLOCKED: Phân môn không thuộc Môn đang chọn.")
        return
    subject_name = _display_name(subject_by[sid], fallback=sid)
    component_name = "Mặc định của môn" if not cid else _display_name(component_by[cid], fallback=cid)
    st.subheader("Phạm vi điều phối đang xem")
    st.write({"Môn": subject_name, "Mã môn": sid, "Phân môn": component_name, "Mã phân môn": cid or "", "Chế độ": "READ ONLY"})
    lp_status, lp_value = _lesson_plan_effective(client, sid, cid)
    gp_status, gp_value = _grouping_effective(client, sid, cid)
    st.subheader("Cấu hình hiệu lực")
    c1, c2 = st.columns(2)
    with c1:
        _render_lesson_plan_effective(st, status=lp_status, value=lp_value)
    with c2:
        _render_grouping_effective(st, status=gp_status, value=gp_value)
    _g1b_p1b_r3a_render_standardizer_capability_dashboard(
        st,
        subject_ref=sid,
        component_ref=cid,
        status=lp_status,
        value=lp_value,
    )
    st.subheader("Bản đồ phân hệ điều phối")
    st.write({
        "Môn / Phân môn canonical": "READY - selector + fail-closed",
        "Chuẩn hóa giáo án": "READY - effective resolver",
        "Nhóm giáo án": "READY - effective resolver",
        "Mẫu / tài nguyên": "UNKNOWN - chưa chứng minh effective resolver",
        "Kho lưu trữ / Drive / Library": "UNKNOWN - chưa chứng minh effective resolver",
        "Đánh giá": "UNKNOWN - chỉ cho phép readiness/summary sau audit riêng",
        "Chương trình / SGK / PPCT": "UNKNOWN - chưa chứng minh effective resolver",
        "Năng lực": "UNKNOWN - chưa chứng minh effective resolver",
        "Quyền": "NOT SUBJECT-SCOPED YET",
        "Công cụ / feature": "NOT SUBJECT-SCOPED YET",
        "Giao diện": "NOT SUBJECT-SCOPED YET",
    })
    st.caption("Kế thừa chỉ áp dụng khi resolver hiện hữu chứng minh được. Các màn ADMIN cũ, repository, schema và runtime được giữ nguyên.")
