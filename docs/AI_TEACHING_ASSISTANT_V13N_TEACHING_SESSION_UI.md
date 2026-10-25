# MathTeacher AI V13N — Teaching Session UI Integration

## Mục tiêu

V13N đưa `TeachingSessionManager` trở thành nguồn trạng thái thống nhất của một tiết dạy trên giao diện giáo viên.

## Nguyên tắc

- UI không tạo `TeachingAssistantController` riêng cho từng lần rerun.
- Một `TeachingSessionManager` được giữ trong `st.session_state` cho một phiên giáo viên.
- Voice, Avatar, MC Planner và Classroom Executor dùng cùng `manager.controller` và `manager.executor`.
- Lesson draft là nguồn để tạo 4 activity chuẩn: Mở đầu, Hình thành kiến thức mới, Luyện tập, Vận dụng.
- Chỉ thẻ `TEACHER_APPROVED` mới có thể cung cấp câu hỏi/mục tiêu cho phiên.
- Classroom Action vẫn đi qua TeachingSessionManager → Executor → Policy.
- Teacher Override vẫn là cơ chế ưu tiên cao hơn việc thực thi AI.

## UI flow

```text
Bài giảng hiện tại
    ↓
Bắt đầu tiết dạy
    ↓
TeachingSessionManager
    ↓
Activity hiện tại
    ↓
MC / điều phối / Classroom Action
    ↓
Teacher confirmation nếu cần
    ↓
Audit/event trong cùng session_id
    ↓
Chuyển hoạt động
```

## Tương thích

Helper thuần của V13N nằm trong `src/ai_kernel/teaching_session_surface.py` để test không phụ thuộc Streamlit. Module UI chỉ làm nhiệm vụ render.

`src/portal_v2/ui/teaching_session_surface.py` giữ vai trò compatibility re-export.
