"""Stable route metadata for the existing Streamlit navigation.

Renderers remain in their legacy dispatchers during the navigation rollout.
The route ID is independent of the translated sidebar label.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceRoute:
    route_id: str
    label: str
    space: str
    group: str
    visible: bool = True


_TEACHER_ROUTES = (
    ("dashboard", "Tổng quan", "Tổng quan"),
    ("lesson_standard", "Soạn bài cùng chuẩn giáo án", "Thiết kế bài học"),
    ("lesson_management", "Quản lý giáo án", "Thiết kế bài học"),
    ("prompt_library", "Thư viện Prompt & AI", "Học liệu"),
    ("openclaw", "Trợ lý OpenClaw", "Học liệu"),
    ("lesson_weekly", "Soạn bài theo tuần", "Thiết kế bài học"),
    ("lesson_ai", "Soạn bài cùng AI", "Thiết kế bài học"),
    ("weekly_schedule", "Lịch báo giảng & PBSDTB", "Kế hoạch dạy"),
    ("timetable", "Thời khóa biểu", "Kế hoạch dạy"),
    ("my_data", "Dữ liệu của tôi", "Hồ sơ & dữ liệu"),
    ("document_library", "Kho tài liệu", "Học liệu"),
    ("assessment_settings", "Thiết đặt đề kiểm tra", "Đề kiểm tra"),
    ("assessment_blueprint", "Ma trận & bản đặc tả", "Đề kiểm tra"),
    ("question_bank_ai", "AI xây dựng ngân hàng câu hỏi", "Đề kiểm tra"),
    ("classroom", "Lớp học ôn tập", "Lớp học"),
    ("assessment_generate", "Tạo đề kiểm tra", "Đề kiểm tra"),
    ("assessment_math6", "Tạo đề kiểm tra Toán 6", "Đề kiểm tra"),
    ("assessment_export", "Xuất đề kiểm tra", "Đề kiểm tra"),
    ("teacher_settings", "Thiết đặt giáo viên", "Hồ sơ & dữ liệu"),
    ("assessment_math69", "Tạo đề kiểm tra Toán 6–9", "Đề kiểm tra"),
    ("question_studio", "Xưởng câu hỏi", "Đề kiểm tra"),
)

TEACHER_ROUTES = tuple(
    WorkspaceRoute(route_id, label, "teacher", group)
    for route_id, label, group in _TEACHER_ROUTES
) + (
    WorkspaceRoute("lesson_tools_legacy", "Công cụ soạn bài", "teacher", "Thiết kế bài học", False),
    WorkspaceRoute("lesson_standard_v2", "Soạn bài cùng chuẩn giáo án V2", "teacher", "Thiết kế bài học", False),
)


def route_from_label(label: str, *, space: str = "teacher") -> WorkspaceRoute:
    """Resolve a legacy label without accepting unknown or cross-space routes."""
    if not isinstance(label, str):
        raise ValueError("unknown workspace route")
    for route in TEACHER_ROUTES:
        if route.space == space and route.label == label:
            return route
    raise ValueError("unknown workspace route")


def visible_teacher_labels() -> tuple[str, ...]:
    return tuple(route.label for route in TEACHER_ROUTES if route.visible)
