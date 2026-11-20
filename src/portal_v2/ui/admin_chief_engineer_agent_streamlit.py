from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_kernel.chief_engineer_agent import ChiefEngineerAgent
from ai_platform.config import AIPlatformConfig


_RESULT_KEY = "chief_engineer_agent_ui_result"
_DEFAULT_OBJECTIVE = (
    "Kiểm tra trạng thái Git, kiểm kê repository và nêu các vấn đề cần ADMIN xem xét. "
    "Chỉ đọc; không chạy kiểm thử và không chỉnh sửa."
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def render_admin_chief_engineer_agent(st: Any, *, admin_actor: str) -> None:
    """ADMIN-only interface for safe, read-only Chief Engineer Agent runs."""
    if not str(admin_actor).strip():
        raise ValueError("admin_actor is required")

    st.title("AI Agent")
    st.caption(
        "Chief Engineer Agent khảo sát repository theo allow-list. "
        "Giao diện này chỉ chạy các bước đọc; không chạy test, sửa mã, commit hay triển khai."
    )

    config = AIPlatformConfig.from_environment()
    if not config.system_admin_enabled:
        st.warning(
            "AI Agent đang tắt. ADMIN vận hành cần bật `SYSTEM_ADMIN_AI_ENABLED` "
            "trong cấu hình ứng dụng để cho phép gọi AI."
        )

    root = _repository_root()
    if not (root / ".git").exists():
        st.warning(
            "Runtime hiện tại không có metadata Git nên Agent chưa thể kiểm tra repository. "
            "Hãy triển khai ứng dụng với repository checkout đầy đủ."
        )

    with st.form("chief_engineer_agent_run_form", clear_on_submit=False):
        objective = st.text_area(
            "Bạn muốn AI Agent khảo sát điều gì?",
            value=_DEFAULT_OBJECTIVE,
            max_chars=2000,
            height=120,
            help="Agent chỉ được xem Git status/diff, kiểm kê tệp và đọc tệp trong allow-list.",
        )
        submitted = st.form_submit_button(
            "Chạy AI Agent",
            type="primary",
            disabled=not config.system_admin_enabled or not (root / ".git").exists(),
            use_container_width=True,
        )

    if submitted:
        if not objective.strip():
            st.error("Hãy nhập mục tiêu khảo sát.")
        else:
            try:
                with st.spinner("AI Agent đang khảo sát repository…"):
                    agent = ChiefEngineerAgent(
                        repo_root=root,
                        max_cycles=4,
                        max_steps=6,
                        allow_tests=False,
                    )
                    run = agent.run(objective.strip())
                st.session_state[_RESULT_KEY] = {
                    "run_id": run.run_id,
                    "status": run.status.value,
                    "cycles": run.cycle_count,
                    "stop_reason": run.stop_reason,
                    "approval_ids": list(run.approval_ids),
                    "observations": list(agent.observations),
                }
            except Exception as exc:
                st.error(
                    "Không thể chạy AI Agent. Hãy kiểm tra AI Runtime & Model Center "
                    f"và cấu hình provider. Loại lỗi: {type(exc).__name__}."
                )

    result = st.session_state.get(_RESULT_KEY)
    if not isinstance(result, dict):
        st.info("Nhập mục tiêu rồi chọn **Chạy AI Agent** để bắt đầu.")
        return

    st.markdown("### Kết quả gần nhất")
    columns = st.columns(3)
    columns[0].metric("Trạng thái", str(result.get("status", "unknown")))
    columns[1].metric("Chu kỳ", str(result.get("cycles", 0)))
    columns[2].metric("Approval", str(len(result.get("approval_ids", ()))))
    st.caption(f"Run: `{result.get('run_id', '')}`")
    if result.get("stop_reason"):
        st.write(str(result["stop_reason"]))

    observations = result.get("observations", ())
    if not observations:
        st.info("Run chưa ghi nhận kết quả công cụ.")
        return
    with st.expander("Nhật ký công cụ và kết quả", expanded=True):
        for index, observation in enumerate(observations, start=1):
            if not isinstance(observation, dict):
                continue
            label = str(
                observation.get("tool_id")
                or observation.get("planner_fallback")
                or f"Bước {index}"
            )
            st.markdown(f"**{label}**")
            st.json(observation, expanded=False)
