"""ADMIN workspace for governed canonical competency codes."""

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
        raise RuntimeError("Dữ liệu năng lực trả về không hợp lệ.")
    return [dict(row) for row in data]


class SupabaseCanonicalCompetencyAdminGateway:
    SAVE_RPC = "save_canonical_competency_entity"
    SAVE_LINK_RPC = "save_learning_requirement_competency_link"

    def __init__(self, *, client: Any) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self.client = client

    def list_frameworks(self) -> tuple[dict[str, Any], ...]:
        return tuple(_rows(self.client.table("competency_frameworks").select("*").order("framework_code").execute()))

    def list_domains(self) -> tuple[dict[str, Any], ...]:
        return tuple(_rows(self.client.table("competency_domains").select("*").order("display_order").execute()))

    def list_components(self) -> tuple[dict[str, Any], ...]:
        return tuple(_rows(self.client.table("competency_components").select("*").order("display_order").execute()))

    def list_indicators(self) -> tuple[dict[str, Any], ...]:
        return tuple(_rows(self.client.table("competency_indicators").select("*").order("display_order").execute()))

    def list_requirements(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            _rows(
                self.client.table("assessment_learning_requirements")
                .select("requirement_code,requirement_text,grade_level,status")
                .eq("status", "ACTIVE")
                .order("grade_level")
                .order("requirement_code")
                .execute()
            )
        )

    def save(self, *, entity_type: str, payload: Mapping[str, object]) -> None:
        self.client.rpc(
            self.SAVE_RPC,
            {"target_entity_type": entity_type, "target_payload": dict(payload)},
        ).execute()

    def save_requirement_link(
        self,
        *,
        requirement_code: str,
        indicator_id: str,
        relation_type: str,
        evidence_strength: str,
        rationale: str,
    ) -> None:
        self.client.rpc(
            self.SAVE_LINK_RPC,
            {
                "target_requirement_code": requirement_code,
                "target_competency_indicator_id": indicator_id,
                "target_relation_type": relation_type,
                "target_evidence_strength": evidence_strength,
                "target_rationale": rationale,
                "target_source_version_id": None,
            },
        ).execute()


def _status_label(value: str) -> str:
    return "Đang sử dụng" if value == "ACTIVE" else "Ngừng sử dụng"


def render_admin_competency_catalog(st: Any, *, client: Any) -> None:
    st.title("Bộ mã năng lực")
    st.caption(
        "Quản trị khung năng lực canonical dùng chung: phẩm chất, năng lực "
        "chung, đặc thù môn học, năng lực số và năng lực AI."
    )
    st.info(
        "Mọi thay đổi đi qua RPC quản trị và được ghi lịch sử. Ngừng sử dụng "
        "mã cũ thay vì xóa để bảo toàn đề, giáo án và minh chứng đã phát sinh."
    )
    if client is None:
        st.error("Chưa có kết nối dữ liệu ADMIN.")
        return
    gateway = SupabaseCanonicalCompetencyAdminGateway(client=client)
    try:
        frameworks = gateway.list_frameworks()
        domains = gateway.list_domains()
        components = gateway.list_components()
        indicators = gateway.list_indicators()
        requirements = gateway.list_requirements()
    except Exception as error:
        st.error(f"Không thể tải bộ mã năng lực: {error}")
        return

    metrics = st.columns(4)
    metrics[0].metric("Khung", len(frameworks))
    metrics[1].metric("Nhóm năng lực", len(domains))
    metrics[2].metric("Thành phần", len(components))
    metrics[3].metric("Chỉ báo", len(indicators))

    tabs = st.tabs((
        "Nhóm năng lực",
        "Thành phần",
        "Chỉ báo",
        "Ánh xạ YCCĐ",
        "Tra cứu toàn bộ",
    ))

    with tabs[0]:
        framework_by_label = {
            f"{row.get('framework_code')} — {row.get('framework_name')}": row
            for row in frameworks
        }
        if not framework_by_label:
            st.warning("Chưa có khung năng lực.")
        else:
            framework_label = st.selectbox("Khung năng lực", tuple(framework_by_label))
            group = st.selectbox(
                "Loại năng lực",
                ("GENERAL", "SUBJECT_SPECIFIC", "DIGITAL", "AI", "QUALITY"),
            )
            cols = st.columns(2)
            with cols[0]:
                code = st.text_input("Mã năng lực", placeholder="Ví dụ: NL-MATH-REASONING")
                name = st.text_input("Tên năng lực")
            with cols[1]:
                subject_id = st.selectbox(
                    "Môn canonical",
                    ("", "subject-math", "subject-foreign-language-1"),
                    disabled=group != "SUBJECT_SPECIFIC",
                )
                status = st.selectbox("Trạng thái", ("ACTIVE", "INACTIVE"), format_func=_status_label)
            description = st.text_area("Mô tả")
            if st.button("Lưu nhóm năng lực", type="primary", use_container_width=True):
                try:
                    gateway.save(
                        entity_type="DOMAIN",
                        payload={
                            "competency_domain_id": "competency-" + uuid4().hex,
                            "framework_id": framework_by_label[framework_label]["framework_id"],
                            "competency_code": code,
                            "competency_name": name,
                            "competency_group": group,
                            "subject_id": subject_id,
                            "description": description,
                            "status": status,
                        },
                    )
                except Exception as error:
                    st.error(f"Không thể lưu nhóm năng lực: {error}")
                else:
                    st.success("Đã lưu nhóm năng lực.")
                    st.rerun()

    with tabs[1]:
        domain_by_label = {
            f"{row.get('competency_code')} — {row.get('competency_name')}": row
            for row in domains
        }
        if not domain_by_label:
            st.warning("Chưa có nhóm năng lực.")
        else:
            domain_label = st.selectbox("Nhóm năng lực", tuple(domain_by_label), key="competency_component_domain")
            component_code = st.text_input("Mã thành phần", key="competency_component_code")
            component_name = st.text_input("Tên thành phần", key="competency_component_name")
            component_description = st.text_area("Mô tả thành phần", key="competency_component_description")
            if st.button("Lưu thành phần năng lực", type="primary", use_container_width=True):
                try:
                    gateway.save(
                        entity_type="COMPONENT",
                        payload={
                            "competency_component_id": "competency-component-" + uuid4().hex,
                            "competency_domain_id": domain_by_label[domain_label]["competency_domain_id"],
                            "component_code": component_code,
                            "component_name": component_name,
                            "description": component_description,
                            "status": "ACTIVE",
                        },
                    )
                except Exception as error:
                    st.error(f"Không thể lưu thành phần: {error}")
                else:
                    st.success("Đã lưu thành phần năng lực.")
                    st.rerun()

    with tabs[2]:
        component_by_label = {
            f"{row.get('component_code')} — {row.get('component_name')}": row
            for row in components
        }
        if not component_by_label:
            st.warning("Chưa có thành phần năng lực.")
        else:
            component_label = st.selectbox("Thành phần", tuple(component_by_label))
            indicator_code = st.text_input("Mã chỉ báo")
            indicator_text = st.text_area("Biểu hiện/chỉ báo có thể đánh giá")
            behavior = st.text_area("Hành vi có thể quan sát")
            grade_cols = st.columns(2)
            with grade_cols[0]:
                grade_min = st.number_input("Từ lớp", 1, 12, 6)
            with grade_cols[1]:
                grade_max = st.number_input("Đến lớp", 1, 12, 9)
            strength = st.selectbox("Mức minh chứng", ("DIRECT", "INDIRECT", "CONTEXTUAL"))
            guidance = st.text_area("Hướng dẫn thu thập minh chứng")
            if st.button("Lưu chỉ báo", type="primary", use_container_width=True):
                try:
                    gateway.save(
                        entity_type="INDICATOR",
                        payload={
                            "competency_indicator_id": "competency-indicator-" + uuid4().hex,
                            "competency_component_id": component_by_label[component_label]["competency_component_id"],
                            "indicator_code": indicator_code,
                            "indicator_text": indicator_text,
                            "observable_behavior": behavior,
                            "evidence_guidance": guidance,
                            "grade_min": int(grade_min),
                            "grade_max": int(grade_max),
                            "evidence_strength": strength,
                            "status": "ACTIVE",
                        },
                    )
                except Exception as error:
                    st.error(f"Không thể lưu chỉ báo: {error}")
                else:
                    st.success("Đã lưu chỉ báo năng lực.")
                    st.rerun()

    with tabs[3]:
        requirement_by_label = {
            f"Lớp {row.get('grade_level')} · {row.get('requirement_text')} "
            f"[{row.get('requirement_code')}]": row
            for row in requirements
        }
        indicator_by_label = {
            f"{row.get('indicator_code')} — {row.get('indicator_text')}": row
            for row in indicators
            if row.get("status") == "ACTIVE"
        }
        if not requirement_by_label or not indicator_by_label:
            st.warning("Cần có YCCĐ và chỉ báo ACTIVE trước khi tạo ánh xạ.")
        else:
            requirement_label = st.selectbox("Yêu cầu cần đạt", tuple(requirement_by_label))
            indicator_label = st.selectbox("Chỉ báo năng lực", tuple(indicator_by_label))
            relation_type = st.selectbox("Vai trò", ("PRIMARY", "SUPPORTING", "CONTEXTUAL"))
            link_strength = st.selectbox(
                "Mức minh chứng của liên kết",
                ("DIRECT", "INDIRECT", "CONTEXTUAL"),
                key="competency_link_strength",
            )
            rationale = st.text_area("Căn cứ ánh xạ")
            if st.button("Lưu ánh xạ YCCĐ – năng lực", type="primary", use_container_width=True):
                try:
                    gateway.save_requirement_link(
                        requirement_code=str(requirement_by_label[requirement_label]["requirement_code"]),
                        indicator_id=str(indicator_by_label[indicator_label]["competency_indicator_id"]),
                        relation_type=relation_type,
                        evidence_strength=link_strength,
                        rationale=rationale,
                    )
                except Exception as error:
                    st.error(f"Không thể lưu ánh xạ: {error}")
                else:
                    st.success("Đã lưu ánh xạ YCCĐ – chỉ báo năng lực.")
                    st.rerun()

    with tabs[4]:
        st.dataframe(domains, use_container_width=True, hide_index=True)
        st.dataframe(components, use_container_width=True, hide_index=True)
        st.dataframe(indicators, use_container_width=True, hide_index=True)
