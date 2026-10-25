# MathTeacher AI – Open Source Autonomous Orchestrator V12

## Mục tiêu

V12 bổ sung lớp supervisor để MathTeacher AI có thể tự chạy workflow có giới hạn mà không biến AI thành một actor có quyền tự do.

## Luồng

Task → Planner Provider → SafeAgentPlanner → Approval Queue (nếu có side effect) → SafeAgentRuntime → Observation → cycle tiếp theo.

## Quy tắc bất biến

- Chỉ skill/tool đã được ADMIN đăng ký mới được sử dụng.
- READ_ONLY/ADVISORY có thể tự chạy trong giới hạn cycle/step.
- MUTATING/GOVERNANCE dừng tại Approval Queue.
- Agent không được tự thay Kernel, Governance, Tool Registry hoặc Runtime Model Center.
- max_cycles được giới hạn tối đa 16.
- Mỗi autonomous run có audit_id, plan_ids, approval_ids và agent_run_ids.

## Chuẩn hóa giáo án

Planner có thể lập kế hoạch `document.standardization.audit` tự động. Bất kỳ bước `document.standardization.apply` nào đều dừng và tạo approval request; không có ADMIN approval thì không sửa DOCX.

## Tự cải thiện

V12 không cho agent tự sửa code. Observation chỉ có thể trở thành knowledge/memory qua các gate V5–V7 và ADMIN approval.
