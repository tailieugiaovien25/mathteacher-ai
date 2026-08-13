from dataclasses import dataclass, field


@dataclass
class LessonObjectives:
    """Nội dung mục tiêu của bài học."""

    knowledge: list[str] = field(default_factory=list)
    competencies: list[str] = field(default_factory=list)
    qualities: list[str] = field(default_factory=list)


@dataclass
class TeachingResources:
    """Thiết bị dạy học và học liệu."""

    teacher: list[str] = field(default_factory=list)
    students: list[str] = field(default_factory=list)


@dataclass
class OrganizationStep:
    """Một bước trong quá trình tổ chức hoạt động."""

    title: str
    teacher_student_activity: str = ""
    expected_product: str = ""


@dataclass
class LearningActivity:
    """Nội dung của một hoạt động dạy học."""

    key: str
    title: str

    objective: str = ""
    content: str = ""
    product: str = ""

    organization_layout: str = "single"

    organization_steps: list[OrganizationStep] = field(
        default_factory=list
    )

    subactivities: list["LearningActivity"] = field(
        default_factory=list
    )


@dataclass
class LessonPlanContent:
    """Nội dung hoàn chỉnh của một giáo án."""

    subject: str
    grade: str
    lesson_name: str

    total_periods: int = 1

    objectives: LessonObjectives = field(
        default_factory=LessonObjectives
    )

    resources: TeachingResources = field(
        default_factory=TeachingResources
    )

    activities: list[LearningActivity] = field(
        default_factory=list
    )

    metadata: dict[str, object] = field(
        default_factory=dict
    )