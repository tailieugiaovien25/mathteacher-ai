from __future__ import annotations

from ai_kernel import AutonomousRunStatus, JSONAutonomousRunStore


def render_admin_ai_autonomous_center(st, *, admin_actor: str) -> None:
    """ADMIN-only observation/control surface for bounded autonomous AI runs."""
    if not str(admin_actor).strip():
        raise ValueError("admin_actor is required")

    store = JSONAutonomousRunStore()
    runs = store.all()
    st.title("AI Autonomous Control Center")
    st.caption(
        "ADMIN theo dõi các AI workflow tự chạy có giới hạn. "
        "Agent không tự cấp quyền, không tự đổi model và mọi side effect vẫn đi qua Approval Center."
    )

    cols = st.columns(5)
    cols[0].metric("Đang chờ duyệt", sum(item.status is AutonomousRunStatus.WAITING_APPROVAL for item in runs))
    cols[1].metric("Hoàn thành", sum(item.status is AutonomousRunStatus.COMPLETED for item in runs))
    cols[2].metric("Bị chặn", sum(item.status is AutonomousRunStatus.BLOCKED for item in runs))
    cols[3].metric("Thất bại", sum(item.status is AutonomousRunStatus.FAILED for item in runs))
    cols[4].metric("Tổng run", len(runs))

    if not runs:
        st.info("Chưa có autonomous run nào.")
        return

    st.dataframe(
        [
            {
                "Run": item.run_id,
                "Task": item.task_id,
                "Skill": item.skill_id,
                "Owner": item.owner.value,
                "Status": item.status.value,
                "Cycles": f"{item.cycle_count}/{item.max_cycles}",
                "Plans": len(item.plan_ids),
                "Approvals": len(item.approval_ids),
                "Agent runs": len(item.agent_run_ids),
                "Audit": item.audit_id,
                "Stop reason": item.stop_reason,
            }
            for item in reversed(runs)
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.info(
        "V12 chỉ cung cấp supervisor bounded: READ_ONLY/ADVISORY có thể chạy tự động; "
        "MUTATING/GOVERNANCE dừng và tạo Approval Request. Việc APPROVE/REJECT thực hiện tại AI Approval Center."
    )
