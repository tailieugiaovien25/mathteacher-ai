from dataclasses import dataclass
from typing import Any


VALID_STEP_TYPES = {
    "CHUYEN_GIAO",
    "THUC_HIEN",
    "BAO_CAO_THAO_LUAN",
    "KET_LUAN",
    "KHAC",
}


@dataclass
class ImplementationStep:
    """
    Một bước tổ chức thực hiện trong hoạt động dạy học.

    Đây là dữ liệu semantic, không phụ thuộc mẫu trình bày.
    Template sau này quyết định:
    - hiển thị dạng bảng hay văn bản;
    - có bao nhiêu cột;
    - tên các cột là gì;
    - trường dữ liệu nào được đưa vào cột nào.
    """

    step_id: str
    step_order: int
    step_type: str

    instruction: str = ""
    teacher_action: str = ""
    student_action: str = ""
    expected_result: str = ""
    content: str = ""
    note: str = ""

    def validate(self) -> None:
        # -----------------------------------------------------
        # 1. STEP_ID
        # -----------------------------------------------------

        if not self._clean_text(
            self.step_id
        ):
            raise ValueError(
                "STEP_ID không được để trống."
            )

        # -----------------------------------------------------
        # 2. STEP_ORDER
        # -----------------------------------------------------

        try:
            order_number = int(
                self.step_order
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "STEP_ORDER phải là số nguyên."
            ) from error

        if order_number <= 0:
            raise ValueError(
                "STEP_ORDER phải lớn hơn 0."
            )

        # -----------------------------------------------------
        # 3. STEP_TYPE
        # -----------------------------------------------------

        normalized_type = (
            self._clean_text(
                self.step_type
            ).upper()
        )

        if (
            normalized_type
            not in VALID_STEP_TYPES
        ):
            raise ValueError(
                "STEP_TYPE không hợp lệ: "
                f"{self.step_type}"
            )

        # -----------------------------------------------------
        # 4. PHẢI CÓ ÍT NHẤT MỘT NỘI DUNG SEMANTIC
        # -----------------------------------------------------

        semantic_values = [
            self.instruction,
            self.teacher_action,
            self.student_action,
            self.expected_result,
            self.content,
            self.note,
        ]

        if not any(
            self._clean_text(value)
            for value in semantic_values
        ):
            raise ValueError(
                "ImplementationStep phải có "
                "ít nhất một nội dung."
            )

    @property
    def normalized_type(self) -> str:
        return (
            self._clean_text(
                self.step_type
            ).upper()
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        self.validate()

        return {
            "STEP_ID": self.step_id,
            "STEP_ORDER": int(
                self.step_order
            ),
            "STEP_TYPE": (
                self.normalized_type
            ),
            "INSTRUCTION": (
                self.instruction
            ),
            "TEACHER_ACTION": (
                self.teacher_action
            ),
            "STUDENT_ACTION": (
                self.student_action
            ),
            "EXPECTED_RESULT": (
                self.expected_result
            ),
            "CONTENT": (
                self.content
            ),
            "NOTE": (
                self.note
            ),
        }

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return " ".join(
            str(value)
            .strip()
            .split()
        )