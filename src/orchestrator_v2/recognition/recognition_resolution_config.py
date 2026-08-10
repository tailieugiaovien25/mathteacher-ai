from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecognitionResolutionConfig:
    """
    Cấu hình cho Recognition Resolution Policy.

    Mục tiêu:
    - tách các ngưỡng ra khỏi thuật toán;
    - cho phép thay đổi cấu hình mà không sửa lõi;
    - hỗ trợ mở rộng theo module / data type / AI provider sau này.

    Các giá trị dưới đây là contract cấu hình,
    chưa phải quyết định tối ưu cuối cùng cho toàn hệ thống.
    """

    recognized_confidence_threshold: float = 0.80
    ambiguity_margin: float = 0.05
    minimum_authority: float = 0.00

    def __post_init__(self) -> None:
        if not (
            0.0
            <= self.recognized_confidence_threshold
            <= 1.0
        ):
            raise ValueError(
                "recognized_confidence_threshold "
                "must be within [0, 1]"
            )

        if not (
            0.0
            <= self.ambiguity_margin
            <= 1.0
        ):
            raise ValueError(
                "ambiguity_margin must be within [0, 1]"
            )

        if not (
            0.0
            <= self.minimum_authority
            <= 1.0
        ):
            raise ValueError(
                "minimum_authority must be within [0, 1]"
            )