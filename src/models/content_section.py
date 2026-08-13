from dataclasses import dataclass, field
from typing import Any

from models.implementation_step import (
    ImplementationStep,
)


VALID_SOURCES = {
    "SGK",
    "TEACHER",
    "SYSTEM",
}


VALID_STATUSES = {
    "draft",
    "approved",
    "deprecated",
}


@dataclass
class ContentSection:
    """
    Một đề mục nội dung nhỏ bên trong hoạt động
    HINH_THANH_KIEN_THUC.

    Ví dụ khi hiển thị giáo án:

    Hoạt động 2. Hình thành kiến thức

    1. [Tên đề mục SGK]
    2. [Tên đề mục SGK]

    Model này chỉ lưu logic/semantic.
    Không chứa quy định về:
    - số cột;
    - tên cột;
    - bảng;
    - font;
    - định dạng trình bày.
    """

    section_id: str
    lesson_key: str
    section_order: int
    section_title: str

    source: str = "SGK"

    # ---------------------------------------------------------
    # Truy vết
    # ---------------------------------------------------------

    yccd_ids: list[str] = field(
        default_factory=list
    )

    objective_ids: list[str] = field(
        default_factory=list
    )

    # ---------------------------------------------------------
    # a) Mục tiêu
    # b) Nội dung
    # c) Sản phẩm
    # ---------------------------------------------------------

    objective_text: str = ""
    content: str = ""
    expected_product: str = ""

    # ---------------------------------------------------------
    # d) Tổ chức thực hiện
    # ---------------------------------------------------------

    implementation_steps: list[
        ImplementationStep
    ] = field(
        default_factory=list
    )

    # ---------------------------------------------------------
    # Nội dung GV chốt sau đề mục
    # ---------------------------------------------------------

    teacher_conclusion: str = ""

    status: str = "draft"

    def validate(self) -> None:
        # -----------------------------------------------------
        # 1. SECTION_ID
        # -----------------------------------------------------

        if not self._clean_text(
            self.section_id
        ):
            raise ValueError(
                "SECTION_ID không được để trống."
            )

        # -----------------------------------------------------
        # 2. LESSON_KEY
        # -----------------------------------------------------

        if not self._clean_text(
            self.lesson_key
        ):
            raise ValueError(
                "LESSON_KEY không được để trống."
            )

        # -----------------------------------------------------
        # 3. SECTION_ORDER
        # -----------------------------------------------------

        try:
            order_number = int(
                self.section_order
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "SECTION_ORDER phải là số nguyên."
            ) from error

        if order_number <= 0:
            raise ValueError(
                "SECTION_ORDER phải lớn hơn 0."
            )

        # -----------------------------------------------------
        # 4. SECTION_TITLE
        # -----------------------------------------------------

        if not self._clean_text(
            self.section_title
        ):
            raise ValueError(
                "SECTION_TITLE không được để trống."
            )

        # -----------------------------------------------------
        # 5. SOURCE
        # -----------------------------------------------------

        normalized_source = (
            self.normalized_source
        )

        if (
            normalized_source
            not in VALID_SOURCES
        ):
            raise ValueError(
                "SOURCE không hợp lệ: "
                f"{self.source}"
            )

        # -----------------------------------------------------
        # 6. YCCD_IDS
        # -----------------------------------------------------

        self._validate_id_list(
            self.yccd_ids,
            "YCCD_IDS",
        )

        # -----------------------------------------------------
        # 7. OBJECTIVE_IDS
        # -----------------------------------------------------

        self._validate_id_list(
            self.objective_ids,
            "OBJECTIVE_IDS",
        )

        # -----------------------------------------------------
        # 8. IMPLEMENTATION_STEPS
        # -----------------------------------------------------

        step_ids: set[str] = set()
        step_orders: set[int] = set()

        for step in self.implementation_steps:
            if not isinstance(
                step,
                ImplementationStep,
            ):
                raise ValueError(
                    "IMPLEMENTATION_STEPS chỉ được "
                    "chứa ImplementationStep."
                )

            step.validate()

            if step.step_id in step_ids:
                raise ValueError(
                    "STEP_ID bị trùng trong section: "
                    f"{step.step_id}"
                )

            step_ids.add(
                step.step_id
            )

            order = int(
                step.step_order
            )

            if order in step_orders:
                raise ValueError(
                    "STEP_ORDER bị trùng "
                    "trong section: "
                    f"{order}"
                )

            step_orders.add(
                order
            )

        # -----------------------------------------------------
        # 9. GV CHỐT NỘI DUNG
        # -----------------------------------------------------

        if not self._clean_text(
            self.teacher_conclusion
        ):
            raise ValueError(
                "TEACHER_CONCLUSION không được "
                "để trống."
            )

        # -----------------------------------------------------
        # 10. STATUS
        # -----------------------------------------------------

        normalized_status = (
            self._clean_text(
                self.status
            ).lower()
        )

        if (
            normalized_status
            not in VALID_STATUSES
        ):
            raise ValueError(
                "STATUS không hợp lệ: "
                f"{self.status}"
            )

    @property
    def normalized_source(
        self,
    ) -> str:
        return (
            self._clean_text(
                self.source
            ).upper()
        )

    def get_implementation_steps(
        self,
    ) -> list[ImplementationStep]:
        """
        Trả về các bước tổ chức thực hiện
        theo đúng STEP_ORDER.
        """

        self.validate()

        return sorted(
            self.implementation_steps,
            key=lambda item: int(
                item.step_order
            ),
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        self.validate()

        return {
            "SECTION_ID": (
                self.section_id
            ),
            "LESSON_KEY": (
                self.lesson_key
            ),
            "SECTION_ORDER": int(
                self.section_order
            ),
            "SECTION_TITLE": (
                self.section_title
            ),
            "SOURCE": (
                self.normalized_source
            ),
            "YCCD_IDS": list(
                self.yccd_ids
            ),
            "OBJECTIVE_IDS": list(
                self.objective_ids
            ),
            "OBJECTIVE_TEXT": (
                self.objective_text
            ),
            "CONTENT": (
                self.content
            ),
            "EXPECTED_PRODUCT": (
                self.expected_product
            ),
            "IMPLEMENTATION_STEPS": [
                step.to_dict()
                for step
                in self.get_implementation_steps()
            ],
            "TEACHER_CONCLUSION": (
                self.teacher_conclusion
            ),
            "STATUS": (
                self.status.lower()
            ),
        }

    @classmethod
    def _validate_id_list(
        cls,
        values: list[str],
        field_name: str,
    ) -> None:
        normalized: list[str] = []

        for value in values:
            cleaned = cls._clean_text(
                value
            )

            if not cleaned:
                raise ValueError(
                    f"{field_name} "
                    "không được chứa ID rỗng."
                )

            normalized.append(
                cleaned
            )

        if (
            len(normalized)
            != len(set(normalized))
        ):
            raise ValueError(
                f"{field_name} "
                "không được chứa ID trùng."
            )

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