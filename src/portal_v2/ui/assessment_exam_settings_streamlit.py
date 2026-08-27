"""Versioned, data-configured assessment settings for teachers and ADMIN."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID


def _data(response: object) -> object:
    if isinstance(response, Mapping):
        return response.get("data")
    return getattr(response, "data", None)


def _rows(response: object) -> list[dict[str, Any]]:
    value = _data(response)
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    if not isinstance(value, list):
        raise ValueError("Supabase không trả về danh sách hợp lệ.")
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _first_scalar(response: object, default: object = None) -> object:
    value = _data(response)
    if isinstance(value, list):
        if not value:
            return default
        value = value[0]
    if isinstance(value, Mapping):
        return next(iter(value.values()), default)
    return default if value is None else value


def _json_object(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _json_list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


class SupabaseAssessmentExamSettingsCatalog:
    SAVE_RPC = "save_assessment_exam_setting_draft"
    SUBMIT_RPC = "submit_assessment_exam_setting_for_review"
    REVIEW_RPC = "review_assessment_exam_setting"

    def __init__(self, *, client: Any, user_id: str) -> None:
        self.client = client
        self.user_id = str(UUID(str(user_id).strip()))

    def default_preset(self) -> dict[str, Any]:
        response = (
            self.client.table("assessment_exam_setting_presets")
            .select(
                "preset_code,preset_name,profile_code,version_number,"
                "default_values"
            )
            .eq("status", "ACTIVE")
            .eq("is_default", True)
            .limit(1)
            .execute()
        )
        rows = _rows(response)
        return rows[0] if rows else {}

    def active_profiles(self) -> list[dict[str, Any]]:
        return _rows(
            self.client.table("assessment_profiles")
            .select(
                "profile_code,profile_name,subject_code,grade_min,"
                "grade_max,total_score,duration_minutes,status"
            )
            .eq("status", "ACTIVE")
            .order("subject_code")
            .order("profile_code")
            .execute()
        )

    def active_textbooks(self) -> list[dict[str, Any]]:
        return _rows(
            self.client.table("textbook_catalog")
            .select(
                "textbook_id,title,textbook_family_code,edition_label,"
                "publication_year,volume_code,status"
            )
            .eq("status", "ACTIVE")
            .order("display_order")
            .order("title")
            .execute()
        )

    def textbook_units(self, textbook_id: str) -> list[dict[str, Any]]:
        if not textbook_id:
            return []
        return _rows(
            self.client.table("textbook_units")
            .select(
                "textbook_unit_id,title,canonical_code,unit_type,"
                "curriculum_period_from,curriculum_period_to,status"
            )
            .eq("textbook_id", textbook_id)
            .eq("status", "ACTIVE")
            .order("display_order")
            .execute()
        )

    def requirements(
        self, *, subject_code: str, grade_level: int
    ) -> list[dict[str, Any]]:
        return _rows(
            self.client.table("assessment_learning_requirements")
            .select(
                "requirement_code,requirement_text,topic_code,"
                "assessment_curriculum_programs!inner(subject_code)"
            )
            .eq("grade_level", grade_level)
            .eq("status", "ACTIVE")
            .eq("assessment_curriculum_programs.subject_code", subject_code)
            .order("requirement_code")
            .execute()
        )

    def save(self, payload: Mapping[str, object]) -> dict[str, Any]:
        rows = _rows(self.client.rpc(self.SAVE_RPC, dict(payload)).execute())
        if len(rows) != 1:
            raise ValueError("RPC lưu thiết đặt phải trả về đúng một phiên bản.")
        return rows[0]

    def submit(self, setting_version_id: str) -> None:
        self.client.rpc(
            self.SUBMIT_RPC,
            {"target_setting_version_id": setting_version_id},
        ).execute()

    def is_admin(self) -> bool:
        return bool(
            _first_scalar(
                self.client.rpc(
                    "assessment_settings_current_user_is_admin", {}
                ).execute(),
                False,
            )
        )

    def pending_reviews(self) -> list[dict[str, Any]]:
        return _rows(
            self.client.table("assessment_exam_setting_versions")
            .select(
                "setting_version_id,version_number,assessment_name,"
                "subject_code,grade_level,academic_year,total_score,"
                "duration_minutes,assessment_exam_setting_sets!inner("
                "setting_code,setting_name,owner_user_id,visibility)"
            )
            .eq("review_status", "PENDING_REVIEW")
            .is_("locked_at", "null")
            .order("updated_at")
            .execute()
        )

    def review(
        self, *, setting_version_id: str, decision: str, note: str
    ) -> None:
        self.client.rpc(
            self.REVIEW_RPC,
            {
                "target_setting_version_id": setting_version_id,
                "target_decision": decision,
                "target_review_note": note,
            },
        ).execute()


def _default_competency_targets(values: Mapping[str, object]) -> list[dict[str, Any]]:
    rows = _json_list(values.get("competency_targets"))
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def render_assessment_exam_settings_page(
    *, st: Any, client: Any, user_id: str
) -> None:
    st.title("Thiết đặt đề kiểm tra")
    st.caption(
        "Cấu hình phạm vi dạy học, SGK, YCCĐ, phẩm chất, năng lực và "
        "chính sách tạo đề bằng dữ liệu có phiên bản."
    )
    st.info(
        "YCCĐ xác định chuẩn cần đánh giá; SGK và PPCT xác định nội dung "
        "đã dạy. Phẩm chất hoặc năng lực số chỉ được ghi nhận khi có "
        "minh chứng phù hợp."
    )
    try:
        catalog = SupabaseAssessmentExamSettingsCatalog(
            client=client, user_id=user_id
        )
        preset = catalog.default_preset()
        profiles = catalog.active_profiles()
        textbooks = catalog.active_textbooks()
    except Exception as error:
        st.error(f"Không thể tải thiết đặt đề kiểm tra: {error}")
        return
    if not profiles:
        st.warning("Chưa có hồ sơ đánh giá ACTIVE.")
        return

    preset_values = _json_object(preset.get("default_values"))
    if preset:
        st.success(
            "Đang dùng preset mặc định: "
            + str(preset.get("preset_name", ""))
        )

    st.subheader("1. Thông tin và cấu trúc đề")
    profile_by_label = {
        f"{row['profile_name']} [{row['profile_code']}]": row
        for row in profiles
    }
    preset_profile = str(preset.get("profile_code", ""))
    profile_labels = tuple(profile_by_label)
    profile_index = next(
        (
            index for index, label in enumerate(profile_labels)
            if str(profile_by_label[label].get("profile_code"))
            == preset_profile
        ),
        0,
    )
    profile_label = st.selectbox(
        "Hồ sơ cấu trúc đề",
        profile_labels,
        index=profile_index,
        key="assessment_setting_profile",
    )
    profile = profile_by_label[profile_label]
    columns = st.columns(2)
    with columns[0]:
        setting_code = st.text_input(
            "Mã thiết đặt", value="TOAN-THCS-CA-NHAN-V1", max_chars=140
        )
        setting_name = st.text_input(
            "Tên thiết đặt", value="Thiết đặt đề kiểm tra của giáo viên"
        )
        assessment_name = st.text_input(
            "Tên bài kiểm tra",
            value=str(
                preset_values.get(
                    "assessment_name", "Kiểm tra định kỳ môn Toán THCS"
                )
            ),
        )
        academic_year = st.text_input("Năm học", value="2026-2027")
    with columns[1]:
        grade_level = st.selectbox(
            "Khối lớp",
            tuple(
                range(
                    int(profile.get("grade_min", 1)),
                    int(profile.get("grade_max", 12)) + 1,
                )
            ),
        )
        semester_number = st.selectbox(
            "Học kỳ", (1, 2, 3),
            index=max(0, int(preset_values.get("semester_number", 1)) - 1),
        )
        duration_minutes = st.number_input(
            "Thời lượng (phút)", min_value=1,
            value=int(profile.get("duration_minutes", 90)),
        )
        total_score = st.number_input(
            "Tổng điểm", min_value=0.25,
            value=float(profile.get("total_score", 10)), step=0.25,
        )
    visibility = st.selectbox(
        "Phạm vi sử dụng", ("PERSONAL", "SHARED"),
        help="SHARED chỉ ADMIN được phép tạo và kích hoạt.",
    )

    st.subheader("2. SGK, PPCT và tiến độ thực dạy")
    textbook_by_label = {"Không ràng buộc một SGK": ""}
    for row in textbooks:
        label = f"{row.get('title')} · {row.get('edition_label') or ''}"
        textbook_by_label[label] = str(row.get("textbook_id", ""))
    textbook_label = st.selectbox("Bộ sách/SGK", tuple(textbook_by_label))
    textbook_id = textbook_by_label[textbook_label]
    try:
        units = catalog.textbook_units(textbook_id)
    except Exception as error:
        st.error(f"Không thể tải bài học SGK: {error}")
        return
    unit_by_label = {
        f"{row.get('title')} [{row.get('canonical_code')}]": str(
            row.get("textbook_unit_id", "")
        )
        for row in units
    }
    selected_unit_labels = st.multiselect(
        "Bài/chủ đề SGK đã dạy", tuple(unit_by_label)
    )
    ppct_reference = st.text_input(
        "Tham chiếu PPCT", placeholder="Mã/phiên bản PPCT đang áp dụng"
    )
    teaching_cutoff_date = st.date_input(
        "Ngày chốt nội dung đã dạy", value=date.today()
    )
    class_codes_text = st.text_input(
        "Lớp áp dụng", placeholder="6A1, 6A2, 6A3"
    )
    only_taught = st.checkbox("Chỉ lấy nội dung đã dạy", value=True)
    common_scope = st.selectbox(
        "Phạm vi khi kiểm tra nhiều lớp",
        ("INTERSECTION", "UNION_WITH_ADMIN_EXCEPTION"),
    )
    include_descendants = st.checkbox(
        "Bao gồm chủ đề con của phạm vi đã chọn", value=True
    )

    st.subheader("3. Yêu cầu cần đạt")
    try:
        requirements = catalog.requirements(
            subject_code=str(profile.get("subject_code", "")),
            grade_level=int(grade_level),
        )
    except Exception as error:
        st.error(f"Không thể tải YCCĐ: {error}")
        return
    requirement_by_label = {
        f"{row.get('requirement_text')} [{row.get('requirement_code')}]": str(
            row.get("requirement_code", "")
        )
        for row in requirements
    }
    selected_requirement_labels = st.multiselect(
        "YCCĐ thuộc phạm vi kiểm tra", tuple(requirement_by_label)
    )

    st.subheader("4. Phẩm chất và năng lực")
    st.caption(
        "DIRECT: minh chứng trực tiếp; INDIRECT: hỗ trợ; CONTEXTUAL: "
        "chỉ xuất hiện trong bối cảnh, không dùng riêng để kết luận."
    )
    competency_targets = st.data_editor(
        _default_competency_targets(preset_values),
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="assessment_setting_competency_targets",
    )

    st.subheader("5. Chính sách tạo và xuất đề")
    policy_columns = st.columns(2)
    with policy_columns[0]:
        approved_only = st.checkbox(
            "Chỉ dùng câu hỏi APPROVED và đã khóa", value=True
        )
        avoid_recent = st.checkbox(
            "Ưu tiên tránh câu đã dùng gần đây", value=True
        )
        avoid_variant_duplicates = st.checkbox(
            "Không trùng câu giữa các mã đề", value=True
        )
        variant_count = st.number_input(
            "Số mã đề", min_value=1, max_value=20,
            value=int(_json_object(
                preset_values.get("question_selection_policy")
            ).get("variant_count", 2)),
        )
    with policy_columns[1]:
        export_matrix = st.checkbox("Xuất ma trận", value=True)
        export_specification = st.checkbox("Xuất bản đặc tả", value=True)
        export_exam = st.checkbox("Xuất đề", value=True)
        export_answer = st.checkbox("Xuất đáp án/HDC", value=True)

    if st.button(
        "Lưu bản nháp thiết đặt", type="primary", use_container_width=True
    ):
        payload = {
            "target_setting_code": setting_code,
            "target_setting_name": setting_name,
            "target_visibility": visibility,
            "target_profile_code": str(profile.get("profile_code", "")),
            "target_subject_code": str(profile.get("subject_code", "")),
            "target_grade_level": int(grade_level),
            "target_assessment_name": assessment_name,
            "target_academic_year": academic_year,
            "target_semester_number": int(semester_number),
            "target_duration_minutes": int(duration_minutes),
            "target_total_score": str(Decimal(str(total_score))),
            "target_textbook_id": textbook_id or None,
            "target_ppct_reference": ppct_reference,
            "target_teaching_cutoff_date": teaching_cutoff_date.isoformat(),
            "target_class_codes": [
                item.strip() for item in class_codes_text.split(",")
                if item.strip()
            ],
            "target_textbook_unit_ids": [
                unit_by_label[label] for label in selected_unit_labels
            ],
            "target_requirement_codes": [
                requirement_by_label[label]
                for label in selected_requirement_labels
            ],
            "target_teaching_scope_policy": {
                "only_taught_content": only_taught,
                "multi_class_scope": common_scope,
                "include_topic_descendants": include_descendants,
                "textbook_is_context_not_authority": True,
            },
            "target_competency_targets": [dict(row) for row in competency_targets],
            "target_question_selection_policy": {
                "approved_and_locked_only": approved_only,
                "avoid_recent_reuse": avoid_recent,
                "avoid_cross_variant_duplicates": avoid_variant_duplicates,
                "variant_count": int(variant_count),
            },
            "target_export_policy": {
                "export_matrix": export_matrix,
                "export_specification": export_specification,
                "export_exam": export_exam,
                "export_answer_key": export_answer,
                "export_marking_guide": export_answer,
            },
        }
        try:
            saved = catalog.save(payload)
        except Exception as error:
            st.error(f"Không thể lưu thiết đặt: {error}")
        else:
            st.session_state["assessment_setting_version_id"] = str(
                saved.get("setting_version_id", "")
            )
            st.success("Đã lưu bản nháp thiết đặt đề kiểm tra.")

    saved_version_id = str(
        st.session_state.get("assessment_setting_version_id", "")
    )
    if st.button(
        "Gửi thiết đặt để duyệt",
        use_container_width=True,
        disabled=not saved_version_id,
    ):
        try:
            catalog.submit(saved_version_id)
        except Exception as error:
            st.error(f"Không thể gửi thiết đặt để duyệt: {error}")
        else:
            st.session_state.pop("assessment_setting_version_id", None)
            st.success("Đã gửi thiết đặt cho ADMIN duyệt.")
            st.rerun()

    try:
        is_admin = catalog.is_admin()
    except Exception:
        is_admin = False
    if not is_admin:
        return
    st.divider()
    st.subheader("6. ADMIN duyệt thiết đặt")
    try:
        pending = catalog.pending_reviews()
    except Exception as error:
        st.error(f"Không thể tải hàng đợi duyệt: {error}")
        return
    if not pending:
        st.info("Không có thiết đặt nào đang chờ duyệt.")
        return
    pending_by_label = {}
    for row in pending:
        relation = row.get("assessment_exam_setting_sets")
        setting_set = relation[0] if isinstance(relation, list) else relation
        setting_set = setting_set if isinstance(setting_set, Mapping) else {}
        label = (
            f"{setting_set.get('setting_name')} · {row.get('assessment_name')} "
            f"· Lớp {row.get('grade_level')} · v{row.get('version_number')}"
        )
        pending_by_label[label] = (row, setting_set)
    pending_label = st.selectbox("Thiết đặt chờ duyệt", tuple(pending_by_label))
    pending_row, pending_set = pending_by_label[pending_label]
    own_setting = str(pending_set.get("owner_user_id", "")) == catalog.user_id
    if own_setting:
        st.warning("ADMIN không được tự duyệt thiết đặt do mình sở hữu.")
    decision_map = {
        "Phê duyệt": "APPROVED",
        "Yêu cầu chỉnh sửa": "REVISION_REQUIRED",
        "Từ chối": "REJECTED",
    }
    decision_label = st.selectbox("Quyết định", tuple(decision_map))
    review_note = st.text_area(
        "Nhận xét", value="Thiết đặt đủ điều kiện áp dụng."
    )
    if st.button(
        "Ghi quyết định duyệt thiết đặt",
        type="primary",
        use_container_width=True,
        disabled=own_setting,
    ):
        try:
            catalog.review(
                setting_version_id=str(pending_row.get("setting_version_id")),
                decision=decision_map[decision_label],
                note=review_note,
            )
        except Exception as error:
            st.error(f"Không thể duyệt thiết đặt: {error}")
        else:
            st.success("Đã ghi quyết định duyệt thiết đặt.")
            st.rerun()
