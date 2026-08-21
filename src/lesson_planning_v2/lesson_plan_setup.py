from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum


class DraftingWeekday(str, Enum):
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

    @property
    def python_weekday(self) -> int:
        return {
            DraftingWeekday.THURSDAY: 3,
            DraftingWeekday.FRIDAY: 4,
            DraftingWeekday.SATURDAY: 5,
            DraftingWeekday.SUNDAY: 6,
        }[self]


class LessonPlanAlignment(str, Enum):
    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"
    JUSTIFY = "JUSTIFY"


@dataclass(frozen=True)
class LessonPlanSchedulingPolicy:
    """
    Quy tắc thời gian dùng chung cho giáo án.

    - Tất cả giáo án trong cùng tuần học dùng chung ngày soạn.
    - Tuần học được xác định bởi Thứ Hai đầu tuần.
    - Ngày soạn nằm ở Thứ 5 / 6 / 7 / Chủ nhật tuần trước.
    - Ngày duyệt = ngày soạn + approval_offset_days.
    - Ngày dạy KHÔNG được tính tại đây; ngày dạy lấy từ
      Lịch báo giảng / TKB theo từng lớp.
    """

    drafting_weekday: DraftingWeekday = (
        DraftingWeekday.SATURDAY
    )

    approval_offset_days: int = 2

    def __post_init__(self) -> None:
        if self.approval_offset_days < 1:
            raise ValueError(
                "approval_offset_days must be >= 1"
            )

    def resolve_drafting_date(
        self,
        *,
        week_start_date: date,
    ) -> date:
        if week_start_date.weekday() != 0:
            raise ValueError(
                "week_start_date must be Monday"
            )

        previous_week_start = (
            week_start_date
            - timedelta(days=7)
        )

        return (
            previous_week_start
            + timedelta(
                days=(
                    self.drafting_weekday
                    .python_weekday
                )
            )
        )

    def resolve_approval_date(
        self,
        *,
        week_start_date: date,
    ) -> date:
        drafting_date = (
            self.resolve_drafting_date(
                week_start_date=week_start_date,
            )
        )

        return (
            drafting_date
            + timedelta(
                days=self.approval_offset_days
            )
        )


@dataclass(frozen=True)
class LessonPlanLayoutProfile:
    """
    Hồ sơ bố cục giáo án.

    Đây là cấu hình trình bày, không chứa dữ liệu bài học.
    """

    profile_name: str = (
        "Giáo án THCS mặc định"
    )

    page_size: str = "A4"

    font_name: str = "Times New Roman"
    body_font_size_pt: float = 14.0
    line_spacing: float = 1.15

    margin_top_cm: float = 2.0
    margin_bottom_cm: float = 2.0
    margin_left_cm: float = 3.0
    margin_right_cm: float = 2.0

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

    approval_alignment: LessonPlanAlignment = (
        LessonPlanAlignment.RIGHT
    )

    approval_label: str = "Tổ CM duyệt"

    approval_signature_blank_lines: int = 5

    def __post_init__(self) -> None:
        if not self.profile_name.strip():
            raise ValueError(
                "profile_name must not be blank"
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

        if (
            self.approval_signature_blank_lines
            < 0
        ):
            raise ValueError(
                "approval_signature_blank_lines "
                "must not be negative"
            )
