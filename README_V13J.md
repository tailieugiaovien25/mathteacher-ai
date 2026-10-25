# MathTeacher AI V13J — Classroom Action Executor

Base: **V13I Classroom Orchestrator**.

## What changed

- Adds `TeachingClassroomActionExecutor` with explicit teacher-in-the-loop execution.
- Adds `StreamlitClassroomRuntime` adapter.
- Adds `InMemoryClassroomRuntime` for deterministic tests.
- Adds `TeachingAssistantController.approve_action()` to record explicit teacher confirmation.
- Updates the AI Teaching Assistant UI with an **Thực hiện** button for each proposed Classroom Action.
- `classroom.slide.open` synchronizes the existing Lesson Designer state key `lesson_slide_selected`.
- Timer, quiz, stage, and whiteboard publish a normalized runtime state/event for classroom surfaces to consume.
- Teacher Override blocks execution immediately.
- Tool/skill allow-lists remain ADMIN-owned; the teacher confirms only individual classroom actions inside the current session.

## Safety boundary

The teacher can confirm classroom actions, but cannot change the AI Kernel, Tool Registry, Skill Registry, model/runtime configuration, or Governance. Those remain ADMIN-controlled.
