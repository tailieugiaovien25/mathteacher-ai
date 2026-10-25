# MathTeacher AI — AI ADMIN Control V3

## Mục tiêu

AI Kernel thuộc quyền quản trị của ADMIN. V3 bổ sung lớp quan sát cấu hình model mà không làm thay đổi Kernel khi dữ liệu/cấu hình thay đổi.

## Nguyên tắc

- Model/provider có thể thay đổi; Kernel contract không đổi.
- Chỉ profile có `admin_enabled=true` mới được sử dụng.
- Nếu cấu hình runtime trỏ tới model chưa được ADMIN bật, hệ thống không tự bật model đó; snapshot dùng profile hợp lệ đầu tiên.
- AI không có quyền sửa Kernel, governance hoặc tự nâng quyền.
- Ollama được kiểm tra qua endpoint local `/api/tags`; không cần cloud API key.

## AI Control Center

Trang `AI Quản trị hệ thống` hiển thị:

- provider/model đang hiệu lực;
- profile đang hiệu lực;
- danh sách profile được ADMIN cho phép;
- khả năng kết nối Ollama local;
- danh sách model thực tế đang có tại Ollama;
- model nào trong local runtime đang được profile hiện hành sử dụng.

Bảng này là **read-only observability**. Việc thay đổi cấu hình vẫn thuộc lớp cấu hình ADMIN.

## Kiểm thử

- AI ADMIN Control V3: 16/16 test mục tiêu PASS khi chạy với `PYTHONPATH=src`.
- Nhóm validation/standardization không phụ thuộc Streamlit: 17/17 PASS.
- `python -m compileall -q src`: PASS.
- Một số UI test không chạy trong môi trường kiểm thử vì môi trường hiện tại thiếu package `streamlit`; đây là giới hạn môi trường, không phải kết luận lỗi V3.
