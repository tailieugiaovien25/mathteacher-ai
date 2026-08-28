"""ADMIN workspace for canonical learning content and textbook alignment."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4


def _rows(response: object) -> list[dict[str, Any]]:
    data = response.get("data") if isinstance(response, Mapping) else getattr(response, "data", None)
    if data is None:
        return []
    if isinstance(data, Mapping):
        return [dict(data)]
    if not isinstance(data, list) or any(not isinstance(row, Mapping) for row in data):
        raise RuntimeError("Dữ liệu nội dung trả về không hợp lệ.")
    return [dict(row) for row in data]


class SupabaseLearningContentAdminGateway:
    def __init__(self, *, client: Any) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self.client = client

    def list_scopes(self) -> tuple[dict[str, Any], ...]:
        return tuple(_rows(self.client.table("education_program_scopes").select(
            "program_id,subject_id,grade_id,status"
        ).eq("status", "ACTIVE").order("subject_id").order("grade_id").execute()))

    def list_contents(self) -> tuple[dict[str, Any], ...]:
        return tuple(_rows(self.client.table("canonical_learning_content_units").select("*")
                           .order("subject_id").order("grade_id").order("display_order").execute()))

    def list_textbook_units(self) -> tuple[dict[str, Any], ...]:
        return tuple(_rows(self.client.table("textbook_units").select(
            "textbook_unit_id,textbook_id,canonical_code,title,unit_type,status"
        ).eq("status", "ACTIVE").order("textbook_id").order("display_order").execute()))

    def list_requirements(self) -> tuple[dict[str, Any], ...]:
        return tuple(_rows(self.client.table("assessment_learning_requirements").select(
            "requirement_code,requirement_text,grade_level,status"
        ).eq("status", "ACTIVE").order("grade_level").order("requirement_code").execute()))

    def save_content(self, payload: Mapping[str, object]) -> None:
        self.client.rpc("save_canonical_learning_content", {"target_payload": dict(payload)}).execute()

    def link_textbook(self, *, content_id: str, textbook_unit_id: str,
                      relation_type: str, coverage_status: str, notes: str) -> None:
        self.client.rpc("save_textbook_content_unit_link", {
            "target_content_unit_id": content_id,
            "target_textbook_unit_id": textbook_unit_id,
            "target_relation_type": relation_type,
            "target_coverage_status": coverage_status,
            "target_notes": notes,
            "target_source_version_id": None,
        }).execute()

    def link_requirement(self, *, requirement_code: str, content_id: str,
                         relation_type: str, alignment_strength: str, rationale: str) -> None:
        self.client.rpc("save_learning_requirement_content_link", {
            "target_requirement_code": requirement_code,
            "target_content_unit_id": content_id,
            "target_relation_type": relation_type,
            "target_alignment_strength": alignment_strength,
            "target_rationale": rationale,
            "target_source_version_id": None,
        }).execute()


def render_admin_learning_content_catalog(st: Any, *, client: Any) -> None:
    st.title("Nội dung dạy học")
    st.caption(
        "Quản trị nội dung canonical và ánh xạ vị trí thể hiện trong từng bộ sách. "
        "Đổi sách giáo khoa không làm thay đổi YCCĐ hoặc mã năng lực."
    )
    st.info(
        "Chỉ lưu mô tả nội dung có nguồn gốc rõ ràng. Văn bản, hình ảnh và audio "
        "có bản quyền tiếp tục được quản trị qua phiên bản nguồn và kho media."
    )
    if client is None:
        st.error("Chưa có kết nối dữ liệu ADMIN.")
        return
    gateway = SupabaseLearningContentAdminGateway(client=client)
    try:
        scopes = gateway.list_scopes()
        contents = gateway.list_contents()
        textbook_units = gateway.list_textbook_units()
        requirements = gateway.list_requirements()
    except Exception as error:
        st.error(f"Không thể tải danh mục nội dung: {error}")
        return

    metrics = st.columns(4)
    metrics[0].metric("Phạm vi môn/lớp", len(scopes))
    metrics[1].metric("Đơn vị nội dung", len(contents))
    metrics[2].metric("Vị trí SGK", len(textbook_units))
    metrics[3].metric("YCCĐ khả dụng", len(requirements))
    tabs = st.tabs(("Đơn vị nội dung", "Ánh xạ sách giáo khoa", "Ánh xạ YCCĐ", "Tra cứu"))

    with tabs[0]:
        scope_by_label = {
            f"{row.get('subject_id')} · {row.get('grade_id')}": row for row in scopes
        }
        if not scope_by_label:
            st.warning("Chưa có phạm vi chương trình ACTIVE.")
        else:
            selected_scope = st.selectbox("Môn và lớp", tuple(scope_by_label))
            scope = scope_by_label[selected_scope]
            cols = st.columns(2)
            with cols[0]:
                content_code = st.text_input("Mã nội dung canonical")
                content_type = st.selectbox("Loại nội dung", (
                    "DOMAIN", "STRAND", "TOPIC", "LESSON", "KNOWLEDGE",
                    "SKILL", "LANGUAGE_FUNCTION", "PRACTICE",
                ))
            with cols[1]:
                title = st.text_input("Tên nội dung")
                lifecycle = st.selectbox("Trạng thái", ("DRAFT", "PENDING_REVIEW", "ACTIVE", "INACTIVE"))
            description = st.text_area("Mô tả chuẩn hóa")
            if st.button("Lưu đơn vị nội dung", type="primary", use_container_width=True):
                try:
                    gateway.save_content({
                        "content_unit_id": "content-" + uuid4().hex,
                        "program_id": scope["program_id"],
                        "subject_id": scope["subject_id"],
                        "grade_id": scope["grade_id"],
                        "content_code": content_code,
                        "content_type": content_type,
                        "title": title,
                        "normalized_description": description,
                        "lifecycle_status": lifecycle,
                    })
                except Exception as error:
                    st.error(f"Không thể lưu nội dung: {error}")
                else:
                    st.success("Đã lưu đơn vị nội dung canonical.")
                    st.rerun()

    active_contents = tuple(row for row in contents if row.get("lifecycle_status") == "ACTIVE")
    content_by_label = {
        f"{row.get('content_code')} — {row.get('title')}": row for row in active_contents
    }
    with tabs[1]:
        unit_by_label = {
            f"{row.get('textbook_id')} · {row.get('canonical_code')} — {row.get('title')}": row
            for row in textbook_units
        }
        if not content_by_label or not unit_by_label:
            st.warning("Cần nội dung canonical và vị trí SGK ACTIVE trước khi ánh xạ.")
        else:
            content_label = st.selectbox("Nội dung canonical", tuple(content_by_label), key="book_content")
            unit_label = st.selectbox("Vị trí trong sách", tuple(unit_by_label))
            relation = st.selectbox("Vai trò vị trí", (
                "PRIMARY_LOCATION", "SUPPORTING_LOCATION", "PRACTICE_LOCATION", "REFERENCE",
            ))
            coverage = st.selectbox("Mức bao phủ", ("FULL", "PARTIAL", "INTRODUCTORY", "EXTENDED"))
            notes = st.text_area("Ghi chú ánh xạ", key="book_notes")
            if st.button("Lưu ánh xạ sách giáo khoa", type="primary", use_container_width=True):
                try:
                    gateway.link_textbook(
                        content_id=content_by_label[content_label]["content_unit_id"],
                        textbook_unit_id=unit_by_label[unit_label]["textbook_unit_id"],
                        relation_type=relation, coverage_status=coverage, notes=notes,
                    )
                except Exception as error:
                    st.error(f"Không thể lưu ánh xạ SGK: {error}")
                else:
                    st.success("Đã liên kết nội dung với vị trí SGK.")

    with tabs[2]:
        requirement_by_label = {
            f"Lớp {row.get('grade_level')} · {row.get('requirement_text')} [{row.get('requirement_code')}]": row
            for row in requirements
        }
        if not content_by_label or not requirement_by_label:
            st.warning("Cần nội dung canonical và YCCĐ ACTIVE trước khi ánh xạ.")
        else:
            requirement_label = st.selectbox("Yêu cầu cần đạt", tuple(requirement_by_label))
            content_label = st.selectbox("Nội dung đáp ứng", tuple(content_by_label), key="requirement_content")
            relation = st.selectbox("Vai trò", ("PRIMARY", "SUPPORTING", "PREREQUISITE", "EXTENSION"))
            strength = st.selectbox("Độ mạnh liên kết", ("DIRECT", "INDIRECT", "CONTEXTUAL"))
            rationale = st.text_area("Căn cứ ánh xạ")
            if st.button("Lưu ánh xạ YCCĐ", type="primary", use_container_width=True):
                try:
                    gateway.link_requirement(
                        requirement_code=requirement_by_label[requirement_label]["requirement_code"],
                        content_id=content_by_label[content_label]["content_unit_id"],
                        relation_type=relation, alignment_strength=strength, rationale=rationale,
                    )
                except Exception as error:
                    st.error(f"Không thể lưu ánh xạ YCCĐ: {error}")
                else:
                    st.success("Đã liên kết nội dung với YCCĐ.")

    with tabs[3]:
        st.dataframe(list(contents), use_container_width=True, hide_index=True)
