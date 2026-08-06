from dataclasses import dataclass, field
from typing import Any


@dataclass
class LessonActivity:
    """Một hoạt động trong tiến trình dạy học."""

    name: str
    objective: str = ""
    teacher_actions: list[str] = field(default_factory=list)
    student_actions: list[str] = field(default_factory=list)
    learning_products: list[str] = field(default_factory=list)
    assessment_methods: list[str] = field(default_factory=list)
    duration_minutes: int | None = None


@dataclass
class LessonModel:
    """Mô hình dữ liệu thống nhất của một bài học."""

    subject: str = ""
    grade: str = ""
    lesson_name: str = ""
    lesson_number: str = ""
    period_count: int | None = None
    duration_minutes: int | None = None

    curriculum: str = ""
    learning_requirements: list[str] = field(default_factory=list)
    objectives: list[str] = field(default_factory=list)

    teaching_methods: list[str] = field(default_factory=list)
    teaching_techniques: list[str] = field(default_factory=list)

    registered_equipment: list[str] = field(default_factory=list)
    learning_resources: list[str] = field(default_factory=list)

    activities: list[LessonActivity] = field(default_factory=list)
    learning_products: list[str] = field(default_factory=list)
    assessment_methods: list[str] = field(default_factory=list)

    source_file: str = ""
    source_sheet: str = ""
    source_row: int | None = None

    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)