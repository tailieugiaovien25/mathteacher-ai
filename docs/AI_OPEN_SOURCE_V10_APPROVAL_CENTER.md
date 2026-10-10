# MathTeacher AI — Open Source AI V10
## ADMIN Approval Center & Traceability

### Mục tiêu
V10 đưa quyền phê duyệt AI có side effect từ backend thành một điểm quản trị thật trong ADMIN Portal.

### Nguyên tắc bất biến
- AI có thể lập kế hoạch nhưng không tự cấp execution token.
- Chỉ ADMIN mới được APPROVE/REJECT thao tác MUTATING/GOVERNANCE.
- Approval phải khớp chính xác task + skill + tool + arguments.
- Kernel và governance không được agent tự sửa.
- Model, dữ liệu, skill, memory và knowledge có thể thay đổi theo version; hệ thống lõi không tự thay đổi.

### Chuỗi truy vết
`approval_id -> plan_id -> agent_run_id -> agent_audit_id -> evaluation_run_id`

`document.standardization.audit` vẫn là read-only/advisory; `document.standardization.operator` mới có quyền gọi transformer và thao tác APPLY vẫn yêu cầu ADMIN approval.

### Giao diện
Trang ADMIN mới: **AI Approval Center**.
- Danh sách pending approval.
- APPROVE / REJECT có actor ADMIN thật.
- Hiển thị task, plan, skill, tool, arguments, risk, rationale.
- Trace approval -> agent run -> evaluation.
- Có trạng thái pending / approved / executed / rejected.

### Tương thích
Approval records cũ không có `plan_id` vẫn đọc được vì field mới có mặc định rỗng.
