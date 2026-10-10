# MathTeacher AI – V13L Lesson Run Validation

## Mục tiêu

Xác nhận một tiết dạy mẫu 4 pha có thể đi qua Teaching Assistant → Classroom Orchestrator → Classroom Action Executor → Presentation Runtime mà không để lại overlay của hoạt động trước, đồng thời Teacher Override chặn AI ngay lập tức.

## Kịch bản

1. Khởi động: slide + quiz + stage + timer.
2. Hình thành kiến thức: dọn overlay → slide + quiz + stage + whiteboard + timer.
3. Luyện tập: dọn overlay → slide + quiz + whiteboard + timer.
4. Giáo viên giành quyền: action AI bị BLOCKED.
5. Giáo viên trả quyền → Vận dụng: dọn overlay → slide + quiz + timer.
6. Dừng timer cuối tiết.

## Thay đổi V13L

Thêm `classroom.surface.clear_overlays` vào policy/tool contract và runtime.

Tool này chỉ xóa các lớp phủ tạm thời (`stage`, `quiz`, `whiteboard`), không thay đổi slide đang chọn và không tự dừng timer. Việc dừng timer vẫn là một action riêng có xác nhận giáo viên.

## Kết quả

- Mô phỏng tiết dạy 4 pha: PASS.
- Teacher Override trong khi đang chạy: BLOCKED như thiết kế.
- Overlay cũ không còn sót sang hoạt động mới sau khi dùng `clear_overlays`.
- Targeted teaching-assistant regression: 17/17 PASS.
- `compileall src`: PASS.
- Regression rộng: 113 PASS / 1 FAIL; ca FAIL là test legacy OpenAI vì môi trường không cài package `openai`, không liên quan V13L.
