from __future__ import annotations

from ai_kernel import AIActionClass, AIOwnership, AIRuntimeManager, JSONAIRuntimeConfigStore, default_model_profiles
from ai_platform.config import AIPlatformConfig


def render_admin_ai_runtime_center(st, *, admin_actor: str) -> None:
    """ADMIN-only control surface for the local AI runtime and model allow-list."""
    config = AIPlatformConfig.from_environment()
    manager = AIRuntimeManager(
        profiles=default_model_profiles(),
        store=JSONAIRuntimeConfigStore(),
        provider=config.provider,
        base_url=config.ollama_base_url,
        selected_profile_id=next(
            (item.profile_id for item in default_model_profiles() if item.provider == config.provider and item.model == config.model),
            "",
        ),
    )
    runtime = manager.inspect_runtime()
    current = manager.config()

    st.title("AI Runtime & Model Center")
    st.caption("Khu vực chỉ ADMIN. Quản lý model local, allow-list và fallback; AI không được tự đổi cấu hình này.")

    cols = st.columns(5)
    cols[0].metric("Provider", runtime.provider)
    cols[1].metric("Endpoint", runtime.base_url)
    cols[2].metric("Runtime", "SẴN SÀNG" if runtime.reachable else "CHƯA KẾT NỐI")
    cols[3].metric("Model active", runtime.active_model)
    cols[4].metric("Đã cài", "Có" if runtime.active_model_installed else "Chưa")

    st.info("V1 của Runtime Center không pull, xóa hoặc cập nhật model tự động. Các thao tác đó vẫn nằm ngoài quyền của AI.")

    profile_ids = [item.profile_id for item in manager.profiles if item.admin_enabled]
    active = st.selectbox(
        "Model profile hoạt động",
        options=profile_ids,
        index=profile_ids.index(current.active_profile_id) if current.active_profile_id in profile_ids else 0,
        format_func=lambda pid: f"{pid} — {manager.resolve_profile(pid).model}",
    )
    enabled = st.multiselect(
        "Model profile được phép",
        options=profile_ids,
        default=list(current.enabled_profile_ids),
        format_func=lambda pid: f"{pid} — {manager.resolve_profile(pid).model}",
    )
    fallbacks = st.multiselect(
        "Fallback profile (chỉ dùng trong kế hoạch; không tự động đổi model ngoài allow-list)",
        options=[pid for pid in enabled if pid != active],
        default=[pid for pid in current.fallback_profile_ids if pid in enabled and pid != active],
        format_func=lambda pid: f"{pid} — {manager.resolve_profile(pid).model}",
    )

    col_a, col_b = st.columns(2)
    if col_a.button("Lưu model active", type="primary"):
        try:
            manager.set_active_profile(active, owner=AIOwnership.ADMIN, admin_actor=admin_actor)
            st.success("Đã cập nhật model active trong lớp cấu hình ADMIN.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if col_b.button("Lưu allow-list + fallback"):
        try:
            manager.set_enabled_profiles(enabled, owner=AIOwnership.ADMIN, admin_actor=admin_actor)
            manager.set_fallback_profiles(fallbacks, owner=AIOwnership.ADMIN, admin_actor=admin_actor)
            st.success("Đã cập nhật allow-list/fallback trong lớp cấu hình ADMIN.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    st.markdown("### Local models")
    if runtime.local_models:
        st.dataframe(
            [
                {"Model local": name, "Active": name == runtime.active_model, "Có trong registry": any(item.model == name for item in manager.profiles)}
                for name in runtime.local_models
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.caption("Chưa đọc được danh sách model local hoặc Ollama chưa chạy.")

    st.markdown("### Registry model")
    st.dataframe(
        [
            {
                "Profile": item.profile_id,
                "Model": item.model,
                "Provider": item.provider,
                "ADMIN bật": item.admin_enabled,
                "Capabilities": ", ".join(sorted(cap.value for cap in item.capabilities)),
                "Allow-list": item.profile_id in current.enabled_profile_ids,
                "Active": item.profile_id == current.active_profile_id,
                "Fallback": item.profile_id in current.fallback_profile_ids,
            }
            for item in manager.profiles
        ],
        hide_index=True,
        use_container_width=True,
    )
