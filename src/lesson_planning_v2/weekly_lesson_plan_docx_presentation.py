from __future__ import annotations

from dataclasses import dataclass


def _required(
    value: str,
    field_name: str,
) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be blank"
        )

    return normalized


@dataclass(frozen=True)
class WeeklyLessonPlanDocxPresentationProfile:
    document_title: str
    teacher_label: str
    subject_label: str
    academic_year_label: str
    week_label: str
    scope_label: str
    curriculum_period_label: str
    preparation_date_label: str
    teaching_date_label: str
    class_label: str
    component_label: str
    objectives_label: str
    materials_label: str
    teaching_process_label: str

    show_document_title: bool = True
    show_component: bool = True
    page_break_between_sections: bool = False
    approval_blank_lines: int = 5

    def __post_init__(self) -> None:
        required_fields = (
            "document_title",
            "teacher_label",
            "subject_label",
            "academic_year_label",
            "week_label",
            "scope_label",
            "curriculum_period_label",
            "preparation_date_label",
            "teaching_date_label",
            "class_label",
            "component_label",
            "objectives_label",
            "materials_label",
            "teaching_process_label",
        )

        for field_name in required_fields:
            object.__setattr__(
                self,
                field_name,
                _required(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if self.approval_blank_lines < 0:
            raise ValueError(
                "approval_blank_lines "
                "must not be negative"
            )
