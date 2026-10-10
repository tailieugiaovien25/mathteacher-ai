from __future__ import annotations

from ai_kernel import AIAdminControl, EvaluationLab, KnowledgeRegistry
from ai_platform.config import AIPlatformConfig
from ai_platform.providers.ollama import OllamaProvider


def render_admin_ai_control_panel(st) -> None:
    """ADMIN-only observability panel for the open-source AI Kernel."""
    config = AIPlatformConfig.from_environment()
    control = AIAdminControl()
    snapshot = control.snapshot(provider=config.provider, model=config.model)

    st.subheader("AI Core — Quyền quản trị ADMIN")
    st.caption(
        "Bảng này chỉ đọc cấu hình runtime hiện hành. AI không có quyền tự đổi Kernel, model hoặc governance."
    )

    cols = st.columns(4)
    cols[0].metric("Provider", snapshot.provider)
    cols[1].metric("Model", snapshot.model)
    cols[2].metric("Profile", snapshot.active_profile_id)
    cols[3].metric("Profile được phép", len(snapshot.enabled_profile_ids))

    if snapshot.provider == "ollama":
        provider = OllamaProvider(base_url=config.ollama_base_url, model=config.model)
        reachable = provider.health()
        cols = st.columns(2)
        cols[0].metric("Ollama local", "SẴN SÀNG" if reachable else "CHƯA KẾT NỐI")
        if reachable:
            try:
                local_models = provider.list_models()
            except Exception as exc:
                local_models = ()
                st.warning(f"Không đọc được danh sách model local: {exc}")
            cols[1].metric("Model local", len(local_models))
            if local_models:
                st.dataframe(
                    [{"Model local": name, "Được ADMIN profile dùng": name == snapshot.model} for name in local_models],
                    hide_index=True,
                    use_container_width=True,
                )
        else:
            cols[1].metric("Endpoint", config.ollama_base_url)

    st.markdown("**Registry model mà Kernel cho phép**")
    rows = []
    for item in control.profiles:
        rows.append(
            {
                "Profile": item.profile_id,
                "Provider": item.provider,
                "Model": item.model,
                "ADMIN bật": "Có" if item.admin_enabled else "Không",
                "Local-first": "Có" if item.local_first else "Không",
                "Capability": ", ".join(sorted(cap.value for cap in item.capabilities)),
            }
        )
    st.dataframe(rows, hide_index=True, use_container_width=True)

    st.markdown("### Registry kỹ năng AI")
    st.caption("Skill là hợp đồng chức năng; ADMIN bật/tắt bằng cấu hình. Kernel không tự tạo hoặc tự cấp quyền cho skill.")
    skill_rows = []
    for skill in control.skills:
        skill_rows.append(
            {
                "Skill": skill.skill_id,
                "Tên": skill.label,
                "Nhóm": skill.domain.value,
                "ADMIN bật": "Có" if skill.admin_enabled else "Không",
                "Action cho phép": ", ".join(sorted(action.value for action in skill.allowed_actions)),
                "Capability": ", ".join(skill.capabilities),
                "Mô tả": skill.description,
            }
        )
    st.dataframe(skill_rows, hide_index=True, use_container_width=True)
    st.markdown("### Registry tri thức — ADMIN kiểm soát phát hành")
    knowledge = KnowledgeRegistry()
    summary = knowledge.summary()
    kcols = st.columns(5)
    kcols[0].metric("Candidate", summary.get("candidate", 0))
    kcols[1].metric("Approved", summary.get("approved", 0))
    kcols[2].metric("Rejected", summary.get("rejected", 0))
    kcols[3].metric("Superseded", summary.get("superseded", 0))
    kcols[4].metric("Revoked", summary.get("revoked", 0))
    st.caption("AI có thể đề xuất candidate; chỉ ADMIN được approve/revoke/supersede. Chỉ knowledge APPROVED được phép làm tri thức dùng chung.")


    st.markdown("### Evaluation Lab — học có kiểm soát")
    eval_summary = EvaluationLab().summary()
    ecols = st.columns(5)
    ecols[0].metric("Runs", eval_summary.get("runs", 0))
    ecols[1].metric("Accepted", eval_summary.get("accepted", 0))
    ecols[2].metric("Review", eval_summary.get("needs_review", 0))
    ecols[3].metric("Rejected", eval_summary.get("rejected", 0))
    ecols[4].metric("Điểm TB", eval_summary.get("average_score", 0.0))
    st.caption("Evaluation Lab chỉ ghi nhận kết quả và đề xuất learning candidate; không tự phát hành knowledge/memory và không sửa Kernel.")

    st.info("Nguyên tắc bất biến: model, dữ liệu, skill và knowledge có thể thay đổi theo phiên bản; AI Kernel và governance không tự thay đổi.")
