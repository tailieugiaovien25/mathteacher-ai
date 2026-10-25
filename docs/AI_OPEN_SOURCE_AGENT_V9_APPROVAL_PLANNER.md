# MathTeacher AI — Open Source AI V9: Approval Queue + Agent Planner

## Mục tiêu

V9 bổ sung hai lớp kiểm soát cho Safe Agent Runtime:

1. **Agent Planner**: biến kế hoạch đề xuất thành các bước `AIToolCall` đã được kiểm tra theo skill/tool allow-list.
2. **Approval Queue**: mọi bước có side effect hoặc yêu cầu approval được đưa vào hàng đợi cho ADMIN; queue không tự thực thi.

## Nguyên tắc bất biến

- Planner không được tạo tool ngoài registry.
- Planner không thực thi tool.
- Tool/skill vẫn do ADMIN bật/tắt.
- `MUTATING`/`GOVERNANCE` luôn yêu cầu approval khi owner không phải ADMIN.
- Approval token là ngẫu nhiên theo từng request; token sai bị từ chối.
- Chỉ ADMIN actor có thể APPROVE/REJECT.
- Queue chỉ là lớp điều phối/quyền; executor vẫn ở `SafeAgentRuntime`.
- Agent không thể dùng approval queue để tự cấp quyền cho chính mình.

## Luồng chuẩn

`Task -> Agent Planner -> Skill/Tool Validation -> Plan -> Approval Queue (nếu cần) -> ADMIN Decision -> Safe Agent Runtime -> Audit`

## Chuẩn hóa giáo án

Agent có thể lập kế hoạch đọc evidence, truy xuất RAG và ghi nhận feedback. Khi plan chạm `document.standardization.apply`, planner đánh dấu `approval_required` và tạo approval request. Không có approval token hợp lệ thì transformer DOCX không được chạy.

## Hướng tiếp theo

- UI cho ADMIN Approval Center.
- Liên kết approval request với `agent_run_id`, `step_id`, `audit_id`.
- Human-in-the-loop cho các bước “review suggested change” trước khi apply.
- Policy theo mức rủi ro và môi trường (`dev/staging/production`).
