from __future__ import annotations

from uuid import uuid4
from curriculum_v2.adapters.supabase_competency_catalog_repository import SupabaseCompetencyCatalogRepository

class SupabaseCompetencyAdminGateway:
    def __init__(self, *, client) -> None:
        if client is None:
            raise ValueError("client must not be None")
        self._client = client

    def save_entity(self, *, entity_type: str, payload: dict) -> None:
        self._client.rpc(
            "save_canonical_competency_entity",
            {
                "target_entity_type": entity_type,
                "target_payload": dict(payload),
            },
        ).execute()

    def save_requirement_link(self, payload: dict) -> None:
        self._client.rpc(
            "save_learning_requirement_competency_link",
            dict(payload),
        ).execute()


def render_admin_competency_catalog(st, *, client) -> None:
    st.title("Quản trị mã năng lực")
    st.caption("Bộ mã canonical mặc định của hệ thống. ADMIN có thể bổ sung, điều chỉnh, ánh xạ và ngừng sử dụng; lịch sử/provenance phải được bảo toàn.")
    if client is None:
        st.error("Chưa có kết nối dữ liệu ADMIN.")
        return
    repo=SupabaseCompetencyCatalogRepository(client=client)
    gateway=SupabaseCompetencyAdminGateway(client=client)
    try:
        frameworks=repo.list_frameworks()
    except Exception as error:
        st.error(f"Không thể tải khung năng lực: {error}")
        return
    framework_options={f"{f.canonical_code} — {f.framework_name}":f for f in frameworks}
    selected_label=st.selectbox("Khung năng lực",tuple(framework_options),key="admin_competency_framework")
    selected=framework_options[selected_label]
    status_filter=st.selectbox("Trạng thái",("Tất cả","ACTIVE","REVIEWED","DRAFT","DEPRECATED","INACTIVE"),key="admin_competency_status")
    try:
        components=repo.list_components(framework_id=selected.framework_id)
        rows=repo.list_indicators(framework_id=selected.framework_id,status=None if status_filter=="Tất cả" else status_filter)
    except Exception as error:
        st.error(f"Không thể tải mã năng lực: {error}")
        return
    metrics=st.columns(4)
    metrics[0].metric("Số chỉ báo",len(rows))
    metrics[1].metric("ACTIVE",sum(x.status=="ACTIVE" for x in rows))
    metrics[2].metric("REVIEWED",sum(x.status=="REVIEWED" for x in rows))
    metrics[3].metric("Không hoạt động",sum(x.status in {"DEPRECATED","INACTIVE"} for x in rows))
    st.dataframe([{
        "Mã hệ thống":x.canonical_code,"Tên/nhóm":x.indicator_name,"Chỉ báo":x.indicator_text,"Mã nguồn":x.source_code or "—",
        "Provenance":x.provenance_status,"Phiên bản":x.version_label,"Trạng thái":x.status,"ID bất biến":x.indicator_id
    } for x in rows],hide_index=True,use_container_width=True)

    st.subheader("Bổ sung mã/chỉ báo")
    with st.form("admin_competency_create_form"):
        component_options={
            f"{c.get('canonical_code','')} — {c.get('component_name','')}":c
            for c in components
        }
        selected_component_label=st.selectbox(
            "Thành phần năng lực",
            tuple(component_options),
            key="admin_competency_create_component",
        ) if component_options else None
        new_code=st.text_input("Mã canonical mới")
        new_name=st.text_input("Tên/nhóm chỉ báo")
        new_text=st.text_area("Nội dung chỉ báo")
        new_source=st.text_input("Mã nguồn (nếu có)")
        submitted=st.form_submit_button("Thêm mới",type="primary")
    if submitted:
        try:
            if not selected_component_label:
                raise ValueError("Khung năng lực chưa có thành phần ACTIVE để gắn chỉ báo.")
            selected_component=component_options[selected_component_label]
            gateway.save_entity(
                entity_type="INDICATOR",
                payload={
                    "indicator_id": f"indicator-admin-{uuid4()}",
                    "framework_id": selected.framework_id,
                    "component_id": str(selected_component["component_id"]),
                    "canonical_code": new_code,
                    "indicator_name": new_name,
                    "indicator_text": new_text,
                    "source_code": new_source or None,
                    "status": "DRAFT",
                    "provenance_status": "UNVERIFIED",
                    "metadata": {"created_via": "ADMIN_COMPETENCY_CATALOG"},
                },
            )
            st.success("Đã thêm mã ở trạng thái DRAFT.")
            st.rerun()
        except Exception as error:
            st.error(f"Không thể thêm mã: {error}")

    if rows:
        st.subheader("Điều chỉnh mã hiện có")
        selected_indicator=st.selectbox("Chọn mã",rows,format_func=lambda x:f"{x.canonical_code} — {x.indicator_name}",key="admin_competency_edit_target")
        with st.form("admin_competency_edit_form"):
            edit_code=st.text_input("Mã canonical",value=selected_indicator.canonical_code)
            edit_name=st.text_input("Tên/nhóm",value=selected_indicator.indicator_name)
            edit_text=st.text_area("Nội dung chỉ báo",value=selected_indicator.indicator_text)
            edit_status=st.selectbox("Trạng thái",("ACTIVE","REVIEWED","DRAFT","DEPRECATED","INACTIVE"),index=("ACTIVE","REVIEWED","DRAFT","DEPRECATED","INACTIVE").index(selected_indicator.status))
            reason=st.text_input("Lý do điều chỉnh (ghi vào metadata/audit context)")
            save=st.form_submit_button("Lưu điều chỉnh")
        if save:
            try:
                metadata=dict(selected_indicator.metadata); metadata["last_admin_reason"]=reason.strip()
                gateway.save_entity(
                    entity_type="INDICATOR",
                    payload={
                        "indicator_id": selected_indicator.indicator_id,
                        "framework_id": selected_indicator.framework_id,
                        "component_id": selected_indicator.component_id,
                        "canonical_code": edit_code.strip(),
                        "source_code": selected_indicator.source_code,
                        "indicator_name": edit_name.strip(),
                        "indicator_text": edit_text.strip(),
                        "observable_flag": selected_indicator.observable_flag,
                        "assessable_flag": selected_indicator.assessable_flag,
                        "version_label": selected_indicator.version_label,
                        "provenance_status": selected_indicator.provenance_status,
                        "status": edit_status,
                        "metadata": metadata,
                    },
                )
                st.success("Đã lưu điều chỉnh; ID bất biến được giữ nguyên.")
                st.rerun()
            except Exception as error:
                st.error(f"Không thể lưu điều chỉnh: {error}")
