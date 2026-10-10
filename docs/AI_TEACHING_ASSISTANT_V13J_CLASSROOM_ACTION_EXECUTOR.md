# MathTeacher AI V13J — Classroom Action Executor

## Mục tiêu

V13J đưa AI Trợ giảng từ **kế hoạch Classroom Action** sang **thực thi có kiểm soát** trong phạm vi lớp học hiện tại.

## Nguyên tắc governance

- ADMIN sở hữu Skill Registry, Tool Registry và policy.
- Giáo viên được quyền xác nhận từng Classroom Action thuộc lớp học đang dạy.
- Giáo viên không có quyền thay đổi AI Kernel, Tool Registry hoặc Governance.
- `MUTATING`/`GOVERNANCE` classroom actions không được tự chạy chỉ vì LLM đã đề xuất.
- Teacher Override có ưu tiên cao nhất: khi giáo viên giành quyền, executor chặn mọi action mới.

## Runtime adapter

`src/ai_kernel/teaching_classroom_executor.py`

Gồm:
- `TeachingClassroomActionExecutor`
- `InMemoryClassroomRuntime`
- `StreamlitClassroomRuntime`
- `ClassroomExecutionResult`

`StreamlitClassroomRuntime` phát event vào `st.session_state` và, với `classroom.slide.open`, đồng bộ trực tiếp `lesson_slide_selected` của Lesson Designer.

Các action còn lại tạo state/event chuẩn hóa để Classroom UI có thể tiêu thụ mà không thay đổi AI Kernel.

## Handoff

```text
TeachingActivityPlan
        ↓
TeachingAssistantController
        ↓
TeachingClassroomActionExecutor
        ↓
Teacher confirmation (nếu MUTATING)
        ↓
ClassroomRuntimePort
        ↓
BÀI GIẢNG / SÂN KHẤU / TIMER / QUIZ / WHITEBOARD
```

## Không làm trong V13J

- Không cấp quyền cho avatar/voice tự gọi executor.
- Không để teacher thay đổi AI governance.
- Không tự chạy các action ngoài `allowed_tool_ids`.
- Không đổi nội dung bài dạy ngoài action contract.
