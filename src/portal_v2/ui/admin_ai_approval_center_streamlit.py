from __future__ import annotations

from collections import defaultdict

from ai_kernel import AIOwnership, ApprovalQueue, ApprovalStatus, JSONAgentRunStore, JSONEvaluationLabStore


def _agent_runs_by_approval(store: JSONAgentRunStore) -> dict[str, list[object]]:
    result: dict[str, list[object]] = defaultdict(list)
    # JSONAgentRunStore is intentionally local-first; expose the same file-backed
    # records through its public path without changing the Kernel contract.
    try:
        import json

        rows = json.loads(store.path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        rows = []
    for row in rows if isinstance(rows, list) else []:
        for step in row.get("steps", ()) if isinstance(row, dict) else ():
            approval_id = str(step.get("approval_id", "") or "") if isinstance(step, dict) else ""
            if approval_id:
                result[approval_id].append(row)
    return result


def _evaluation_runs_for_task(store: JSONEvaluationLabStore, task_id: str) -> tuple[object, ...]:
    return tuple(item for item in store.runs() if item.task_id == task_id)


def render_admin_ai_approval_center(st, *, admin_actor: str) -> None:
    """ADMIN-only approval center for AI agent side effects."""
    if not str(admin_actor).strip():
        raise ValueError("admin_actor is required")

    queue = ApprovalQueue()
    pending = queue.pending()
    all_requests = queue.store.all()

    st.title("AI Approval Center")
    st.caption(
        "Nơi duy nhất để ADMIN phê duyệt các thao tác AI có side effect. "
        "Approval chỉ cấp quyền cho đúng task/skill/tool/arguments đã được kiểm tra."
    )

    metrics = st.columns(5)
    metrics[0].metric("Chờ duyệt", sum(item.status is ApprovalStatus.PENDING for item in all_requests))
    metrics[1].metric("Đã duyệt", sum(item.status is ApprovalStatus.APPROVED for item in all_requests))
    metrics[2].metric("Đã thực thi", sum(item.status is ApprovalStatus.EXECUTED for item in all_requests))
    metrics[3].metric("Từ chối", sum(item.status is ApprovalStatus.REJECTED for item in all_requests))
    metrics[4].metric("Tổng", len(all_requests))

    if pending:
        st.markdown("### Yêu cầu đang chờ ADMIN quyết định")
        for request in pending:
            with st.container(border=True):
                st.markdown(f"**{request.tool_id}** — `{request.approval_id}`")
                cols = st.columns(4)
                cols[0].write(f"**Task:** `{request.task_id}`")
                cols[1].write(f"**Skill:** `{request.skill_id}`")
                cols[2].write(f"**Requester:** `{request.requester.value}`")
                cols[3].write(f"**Risk:** `{request.risk_level}`")
                st.code(str(request.arguments), language="json")
                if request.rationale:
                    st.caption(f"Lý do: {request.rationale}")

                approval_col, reject_col = st.columns(2)
                if approval_col.button("ADMIN phê duyệt", key=f"approve_{request.approval_id}", type="primary"):
                    queue.approve(request.approval_id, admin_actor=admin_actor, actor_owner=AIOwnership.ADMIN)
                    st.success(f"Đã phê duyệt {request.approval_id}.")
                    st.rerun()
                if reject_col.button("Từ chối", key=f"reject_{request.approval_id}"):
                    queue.reject(request.approval_id, admin_actor=admin_actor, actor_owner=AIOwnership.ADMIN, reason="ADMIN từ chối tại Approval Center.")
                    st.warning(f"Đã từ chối {request.approval_id}.")
                    st.rerun()
    else:
        st.info("Hiện không có yêu cầu AI nào đang chờ ADMIN phê duyệt.")

    st.markdown("### Truy vết approval → agent run → evaluation")
    run_store = JSONAgentRunStore()
    run_by_approval = _agent_runs_by_approval(run_store)
    eval_store = JSONEvaluationLabStore()
    trace_rows = []
    for request in all_requests:
        runs = run_by_approval.get(request.approval_id, [])
        evals = _evaluation_runs_for_task(eval_store, request.task_id)
        trace_rows.append(
            {
                "Approval": request.approval_id,
                "Status": request.status.value,
                "Task": request.task_id,
                "Plan": request.plan_id or "—",
                "Skill": request.skill_id,
                "Tool": request.tool_id,
                "Agent run": ", ".join(str(run.get("run_id", "")) for run in runs) or "—",
                "Agent audit": ", ".join(str(run.get("audit_id", "")) for run in runs) or "—",
                "Evaluation": ", ".join(f"{item.run_id}:{item.outcome.value}:{item.score:.2f}" for item in evals) or "—",
                "ADMIN quyết định": request.decided_by or "—",
            }
        )
    st.dataframe(trace_rows, hide_index=True, use_container_width=True)

    st.caption(
        "Nguyên tắc: AI có thể lập kế hoạch; chỉ ADMIN mới cấp execution token cho thao tác MUTATING/GOVERNANCE. "
        "Kernel không tự cấp quyền và không tự thay đổi governance."
    )
