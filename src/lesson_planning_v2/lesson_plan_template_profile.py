from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LessonPlanAlignment(str, Enum):
    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"
    JUSTIFY = "JUSTIFY"


class DraftingWeekday(str, Enum):
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


@dataclass(frozen=True)
class LessonPlanStructureSection:
    key: str
    title: str
    required: bool = True
    enabled: bool = True
    order: int = 0

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError(
                "section key must not be blank"
            )

        if not self.title.strip():
            raise ValueError(
                "section title must not be blank"
            )

        if self.order < 0:
            raise ValueError(
                "section order must not be negative"
            )


@dataclass(frozen=True)
class LessonPlanStructureProfile:
    sections: tuple[
        LessonPlanStructureSection,
        ...
    ]

    @classmethod
    def default(cls):
        return cls(
            sections=(
                LessonPlanStructureSection(
                    key="OBJECTIVES",
                    title="I. MỤC TIÊU",
                    order=10,
                ),
                LessonPlanStructureSection(
                    key="EQUIPMENT",
                    title=(
                        "II. THIẾT BỊ DẠY HỌC "
                        "VÀ HỌC LIỆU"
                    ),
                    order=20,
                ),
                LessonPlanStructureSection(
                    key="TEACHING_PROCESS",
                    title=(
                        "III. TIẾN TRÌNH "
                        "DẠY HỌC"
                    ),
                    order=30,
                ),
                LessonPlanStructureSection(
                    key="OPENING",
                    title="Mở đầu",
                    order=40,
                ),
                LessonPlanStructureSection(
                    key="KNOWLEDGE_FORMATION",
                    title="Hình thành kiến thức",
                    order=50,
                ),
                LessonPlanStructureSection(
                    key="PRACTICE",
                    title="Luyện tập",
                    order=60,
                ),
                LessonPlanStructureSection(
                    key="APPLICATION",
                    title="Vận dụng",
                    order=70,
                ),
            )
        )

    def __post_init__(self) -> None:
        keys = tuple(
            section.key
            for section in self.sections
        )

        if len(keys) != len(set(keys)):
            raise ValueError(
                "duplicate structure section key"
            )


@dataclass(frozen=True)
class LessonPlanHeaderProfile:
    drafting_teaching_alignment: (
        LessonPlanAlignment
    ) = LessonPlanAlignment.LEFT

    period_alignment: LessonPlanAlignment = (
        LessonPlanAlignment.CENTER
    )

    period_bold: bool = True

    lesson_title_alignment: (
        LessonPlanAlignment
    ) = LessonPlanAlignment.CENTER

    lesson_title_uppercase: bool = True
    lesson_title_bold: bool = True


@dataclass(frozen=True)
class LessonPlanLayoutProfile:
    page_size: str = "A4"

    font_name: str = "Times New Roman"
    body_font_size_pt: float = 14.0
    line_spacing: float = 1.15

    margin_top_cm: float = 2.0
    margin_bottom_cm: float = 2.0
    margin_left_cm: float = 3.0
    margin_right_cm: float = 2.0

    def __post_init__(self) -> None:
        if not self.page_size.strip():
            raise ValueError(
                "page_size must not be blank"
            )

        if not self.font_name.strip():
            raise ValueError(
                "font_name must not be blank"
            )

        if self.body_font_size_pt <= 0:
            raise ValueError(
                "body_font_size_pt must be positive"
            )

        if self.line_spacing <= 0:
            raise ValueError(
                "line_spacing must be positive"
            )

        margins = (
            self.margin_top_cm,
            self.margin_bottom_cm,
            self.margin_left_cm,
            self.margin_right_cm,
        )

        if any(
            value < 0
            for value in margins
        ):
            raise ValueError(
                "page margins must not be negative"
            )


@dataclass(frozen=True)
class LessonPlanSchedulingPolicy:
    drafting_weekday: DraftingWeekday = (
        DraftingWeekday.SATURDAY
    )

    approval_offset_days: int = 2

    allow_projected_teaching_dates: bool = True

    projected_schedule_horizon_weeks: int = 2

    def __post_init__(self) -> None:
        if self.approval_offset_days < 1:
            raise ValueError(
                "approval_offset_days must be >= 1"
            )

        if (
            self.projected_schedule_horizon_weeks
            < 0
        ):
            raise ValueError(
                "projected_schedule_horizon_weeks "
                "must not be negative"
            )


@dataclass(frozen=True)
class LessonPlanApprovalProfile:
    alignment: LessonPlanAlignment = (
        LessonPlanAlignment.RIGHT
    )

    approval_label: str = "Tổ CM duyệt"

    signature_blank_lines: int = 5

    def __post_init__(self) -> None:
        if not self.approval_label.strip():
            raise ValueError(
                "approval_label must not be blank"
            )

        if self.signature_blank_lines < 0:
            raise ValueError(
                "signature_blank_lines "
                "must not be negative"
            )


@dataclass(frozen=True)
class LessonPlanTemplateProfile:
    profile_name: str

    structure: LessonPlanStructureProfile
    header: LessonPlanHeaderProfile
    layout: LessonPlanLayoutProfile
    scheduling: LessonPlanSchedulingPolicy
    approval: LessonPlanApprovalProfile

    is_default: bool = False

    @classmethod
    def default(cls):
        return cls(
            profile_name="Mẫu giáo án THCS mặc định",
            structure=(
                LessonPlanStructureProfile
                .default()
            ),
            header=LessonPlanHeaderProfile(),
            layout=LessonPlanLayoutProfile(),
            scheduling=(
                LessonPlanSchedulingPolicy()
            ),
            approval=(
                LessonPlanApprovalProfile()
            ),
            is_default=True,
        )

    def __post_init__(self) -> None:
        if not self.profile_name.strip():
            raise ValueError(
                "profile_name must not be blank"
            )
