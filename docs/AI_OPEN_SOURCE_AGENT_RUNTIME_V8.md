# MathTeacher AI — Open Source AI V8: Safe Agent Runtime

## Mục tiêu

V8 bổ sung một lớp Agent Runtime có giới hạn để MathTeacher AI có thể tự chạy các chuỗi tác vụ đã được ADMIN cho phép mà không biến agent thành một tiến trình có quyền tự do trên hệ thống.

## Nguyên tắc bất biến

- ADMIN sở hữu danh sách skill và tool được phép.
- Agent chỉ được gọi tool đã đăng ký và đang được ADMIN bật.
- Agent không thể import/call Python tùy ý, tự đăng ký tool hoặc tự sửa registry.
- READ_ONLY/ADVISORY có thể chạy tự động trong phạm vi skill.
- MUTATING/GOVERNANCE không tự chạy cho USER/SYSTEM; phải đi qua ADMIN approval.
- Agent bị giới hạn số bước (`max_steps`, tối đa 32) để tránh vòng lặp vô hạn.
- Mọi run và từng step được lưu local-first để audit.
- Tool `document.standardization.apply` là đường dẫn dành cho transformer deterministic; V8 không cho AI tự sửa DOCX.

## Vòng chạy

`Task -> Skill -> Tool Allow-list -> Execute/Approval -> Audit -> Result`

## Chuẩn hóa giáo án

Agent có thể tự thực hiện các bước đọc evidence và truy xuất tri thức APPROVED. Bước thay đổi DOCX chỉ trở thành một tool MUTATING có approval; agent không tự cấp quyền cho mình.

## Hướng mở rộng

V9 có thể bổ sung Approval Queue persistence, Tool Capability Scoping chi tiết hơn và Agent Planner dùng AI Kernel để đề xuất kế hoạch, nhưng planner chỉ được tạo `AIToolCall` trong allow-list; executor vẫn là lớp deterministic.
