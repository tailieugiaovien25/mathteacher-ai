# MathTeacher AI – Open Source AI V6: Memory + Evaluation Gate

## Mục tiêu

V6 bổ sung lớp Memory/RAG local-first và Evaluation Gate mà không thay đổi AI Kernel/governance.

## Nguyên tắc

- Chỉ memory/knowledge ở trạng thái APPROVED mới được đưa vào context dùng chung.
- Candidate được đề xuất bởi AI/system/user nhưng ADMIN mới được publish.
- Trước khi publish memory phải vượt Evaluation Gate deterministic.
- Memory được gắn `skill_id` để không tràn ngữ cảnh giữa các chức năng.
- Retrieval V6 không cần dịch vụ embedding bên ngoài: dùng lexical retrieval deterministic làm baseline.
- Có thể thay bằng vector store/embedding local ở V7 mà không đổi contract Kernel.
- AI không có quyền sửa Kernel, governance hoặc tự cấp quyền.

## Vòng học có kiểm soát

`Task -> Observation -> Candidate Memory -> Evaluation Gate -> ADMIN approval -> Retrieval -> Next task`

AI có thể tích lũy kinh nghiệm, nhưng việc đưa kinh nghiệm vào bộ nhớ dùng chung là một lifecycle có kiểm soát.

## Chuẩn hóa giáo án

Skill `document.standardization.audit` có thể lưu các quy tắc/học liệu/kinh nghiệm đã được duyệt và truy xuất chúng trong các phiên kiểm định tiếp theo. V6 không thay đổi nguyên tắc: AI chỉ phân tích bằng chứng; transformer deterministic mới sửa DOCX.
