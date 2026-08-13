from dataclasses import dataclass, field


@dataclass
class LessonPlanSectionSchema:
    """Mô tả một mục trong mẫu giáo án."""

    key: str
    title: str
    required: bool = True
    order: int = 0


@dataclass
class ActivitySchema:
    """Mô tả cấu trúc của một loại hoạt động dạy học."""

    key: str
    title: str
    default_layout: str = "single"
    allowed_layouts: list[str] = field(
        default_factory=lambda: ["single"]
    )
    allow_subactivities: bool = False

    column_headers: list[str] = field(
        default_factory=list
    )


@dataclass
class LessonPlanSchema:
    """Mô tả một mẫu giáo án có thể cấu hình."""

    schema_id: str
    name: str
    subject: str = ""
    version: str = "1.0"

    sections: list[LessonPlanSectionSchema] = field(
        default_factory=list
    )

    activities: list[ActivitySchema] = field(
        default_factory=list
    )

    metadata: dict[str, object] = field(
        default_factory=dict
    )