from __future__ import annotations

from dataclasses import dataclass


_SUPPORTED_ALIGNMENTS = frozenset(
    {
        "left",
        "center",
        "right",
        "justify",
    }
)


def _required_text(
    value: str,
    field_name: str,
) -> str:
    normalized = str(
        value or ""
    ).strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be blank"
        )

    return normalized


def _positive_number(
    value: float,
    field_name: str,
) -> float:
    if isinstance(value, bool):
        raise ValueError(
            f"{field_name} must be positive"
        )

    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{field_name} must be positive"
        ) from error

    if normalized <= 0:
        raise ValueError(
            f"{field_name} must be positive"
        )

    return normalized


def _non_negative_number(
    value: float,
    field_name: str,
) -> float:
    if isinstance(value, bool):
        raise ValueError(
            f"{field_name} must not be negative"
        )

    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{field_name} must not be negative"
        ) from error

    if normalized < 0:
        raise ValueError(
            f"{field_name} must not be negative"
        )

    return normalized


def _alignment(
    value: str,
    field_name: str,
) -> str:
    normalized = _required_text(
        value,
        field_name,
    ).lower()

    if normalized not in _SUPPORTED_ALIGNMENTS:
        raise ValueError(
            f"{field_name} must be one of: "
            "left, center, right, justify"
        )

    return normalized


@dataclass(frozen=True)
class WeeklyLessonPlanDocxLayoutProfile:
    """
    Presentation-independent DOCX layout policy.

    The renderer consumes this profile instead of
    hard-coding font, size, margins or alignment.
    """

    body_font: str = "Times New Roman"
    body_size: float = 14

    title_size: float = 16
    heading_size: float = 14

    top_margin_cm: float = 2.0
    bottom_margin_cm: float = 2.0
    left_margin_cm: float = 3.0
    right_margin_cm: float = 2.0

    line_spacing: float = 1.15

    space_before_pt: float = 0
    space_after_pt: float = 6

    header_alignment: str = "center"
    approval_alignment: str = "right"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "body_font",
            _required_text(
                self.body_font,
                "body_font",
            ),
        )

        for field_name in (
            "body_size",
            "title_size",
            "heading_size",
            "top_margin_cm",
            "bottom_margin_cm",
            "left_margin_cm",
            "right_margin_cm",
            "line_spacing",
        ):
            object.__setattr__(
                self,
                field_name,
                _positive_number(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                ),
            )

        for field_name in (
            "space_before_pt",
            "space_after_pt",
        ):
            object.__setattr__(
                self,
                field_name,
                _non_negative_number(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                ),
            )

        object.__setattr__(
            self,
            "header_alignment",
            _alignment(
                self.header_alignment,
                "header_alignment",
            ),
        )

        object.__setattr__(
            self,
            "approval_alignment",
            _alignment(
                self.approval_alignment,
                "approval_alignment",
            ),
        )

    @classmethod
    def default(
        cls,
    ) -> "WeeklyLessonPlanDocxLayoutProfile":
        """
        Default professional lesson-plan layout.

        Body:
        Times New Roman, 14 pt.
        """
        return cls()
