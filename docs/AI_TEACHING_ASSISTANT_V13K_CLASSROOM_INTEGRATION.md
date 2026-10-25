# AI Teaching Assistant V13K – Classroom Integration

## Mục tiêu

Nối `TeachingClassroomActionExecutor` vào các bề mặt lớp học thực của MathTeacher AI mà không tạo một runtime lớp học thứ hai.

## Hợp đồng tích hợp

- BÀI GIẢNG: `lesson_slide_selected`
- Sân khấu tích hợp: `lesson_integrated_stages`
- Slide IDs của bài hiện tại: `lesson_slide_ids`
- Runtime state: `ta_classroom_runtime_state_v13k`
- Event: `ta_classroom_runtime_event_v13k`

Các key V13J vẫn được ghi song song để tương thích với test/phiên cũ.

## Các action đã nối

- `classroom.slide.open`
  - Kiểm tra `slide_id` thuộc bài giảng hiện tại nếu danh sách slide đã được xuất bản vào session state.
  - Cập nhật `lesson_slide_selected` và reset `lesson_surface_index`.

- `classroom.stage.show`
  - Yêu cầu `content_id` đã có trong `lesson_integrated_stages` nếu stage cache tồn tại.
  - Vùng trình chiếu dựng overlay stage từ chính HTML stage đã chuẩn bị.

- `classroom.timer.start` / `classroom.timer.stop`
  - Cập nhật runtime state.
  - Presentation surface hiển thị bộ đếm ở phía trình duyệt.

- `classroom.quiz.display`
  - Cập nhật runtime state.
  - Presentation surface hiển thị câu hỏi đã được giáo viên xác nhận.

- `classroom.whiteboard.show`
  - Cập nhật runtime state.
  - Presentation surface hiển thị bảng/nội dung gợi ý.

## Quyền

Mọi action MUTATING vẫn phải đi qua `TeachingClassroomActionExecutor` và xác nhận của giáo viên. Teacher Override chặn executor ngay lập tức.

AI không được thay đổi Kernel, Tool Registry, Skill Registry, model/runtime governance hoặc quyền ADMIN.

## Giới hạn V13K

- Timer/Quiz/Whiteboard đã điều khiển **presentation runtime state và render overlay thật trong vùng Bài giảng**, nhưng chưa thay thế các UI chuyên dụng độc lập của từng tool.
- LiveKit/voice/avatar vẫn là adapter; V13K không mở thêm side effect từ voice layer.
- Test Streamlit UI end-to-end chưa thực hiện trong môi trường hiện tại vì môi trường test thiếu `streamlit`.
