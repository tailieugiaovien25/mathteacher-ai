# MathTeacher AI V13I — AI Teaching Assistant Classroom Orchestrator

## Mục tiêu

V13I đưa AI Trợ giảng từ lớp realtime voice/avatar sang lớp **MC + điều phối hoạt động + đề xuất điều khiển kỹ thuật**, nhưng không cấp cho voice/avatar quyền tự thực thi Classroom Action.

## Nguyên tắc

- AI được lập kịch bản và kế hoạch.
- Mọi thao tác có side effect phải qua Policy/Approval.
- Hoạt động chỉ được dùng tool nằm trong `allowed_tools` của lesson activity.
- Teacher override vẫn có hiệu lực ngay lập tức.
- Tool Registry là allow-list do ADMIN quản trị.
- Kernel/Governance không bị AI sửa.

## Thành phần

### `src/ai_kernel/teaching_classroom.py`

Cung cấp:
- `ClassroomPhase`
- `LessonActivityContext`
- `TeachingScriptLine`
- `TeachingActivityPlan`
- `TeachingClassroomOrchestrator`

Orchestrator tạo:
1. kịch bản lời dẫn MC;
2. các bước điều phối hoạt động;
3. danh sách Classroom Actions đề xuất;
4. cờ `requires_teacher_confirmation`.

### `src/ai_kernel/skills.py`

Bổ sung skill:

`classroom.teaching.orchestrator`

Skill này cho phép lập kế hoạch có các action class READ_ONLY/ADVISORY/MUTATING; side effect vẫn phải đi qua policy.

### `src/ai_kernel/agent_runtime.py`

Đăng ký chính thức các classroom tools:
- `classroom.status.read`
- `classroom.slide.open`
- `classroom.stage.show`
- `classroom.timer.start`
- `classroom.timer.stop`
- `classroom.quiz.display`
- `classroom.whiteboard.show`

Các tool có side effect yêu cầu ADMIN approval ở Safe Agent Runtime.

## Giao diện giáo viên

AI Trợ giảng có thêm vùng **MC & điều phối hoạt động**:
- chọn vai trò MC/điều phối/kỹ thuật/đồng giảng;
- nhập lesson/activity context;
- chọn slide/timer/question proposal;
- tạo kịch bản;
- xem các Classroom Actions được đề xuất;
- chưa thực thi trực tiếp từ UI.

## Kiểm thử

`PYTHONPATH=src pytest -q src/tests/test_ai_*.py src/tests/test_teaching_*.py`

Kết quả V13I:

**98 passed**

`python -m compileall -q src`: **PASS**
