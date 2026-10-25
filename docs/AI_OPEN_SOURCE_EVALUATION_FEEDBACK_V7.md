# MathTeacher AI – Open Source AI V7: Evaluation Lab + Feedback Loop

## Mục tiêu

V7 bổ sung một vòng đánh giá có thể kiểm chứng để hệ thống tích lũy kinh nghiệm mà không tự thay đổi Kernel/Governance.

## Luồng

`Task -> Run -> Evaluation -> Human/System Feedback -> Pattern -> Candidate Memory -> Evaluation Gate -> ADMIN approval -> RAG`

## Quy tắc bất biến

- Evaluation Lab chỉ ghi nhận kết quả/feedback và tạo đề xuất học tập.
- Candidate Memory luôn bắt đầu ở trạng thái `CANDIDATE`.
- Evaluation Lab không được publish memory.
- Skill của candidate luôn được giữ nguyên để tránh tràn ngữ cảnh.
- Chỉ Memory/Knowledge `APPROVED` mới được RAG dùng chung.
- ADMIN vẫn là chủ thể duyệt tri thức và cấu hình AI.
- Kernel/Governance không được sửa bởi feedback hoặc memory.

## Chuẩn hóa giáo án

Các phiên `document.standardization.audit` có thể được ghi thành Evaluation Run. Khi một lỗi/khó khăn lặp lại qua nhiều phản hồi, Evaluation Lab chỉ tạo ra candidate memory mô tả mẫu vấn đề; không tự biến mẫu đó thành quy tắc chuẩn hóa. Quy tắc chính thức vẫn thuộc rule engine/deterministic transformer và quyền duyệt của ADMIN.
