from dataclasses import dataclass, field
from typing import Any

from models.content_section import ContentSection
from models.implementation_step import ImplementationStep


VALID_ACTIVITY_TYPES = {
    "MO_DAU",
    "HINH_THANH_KIEN_THUC",
    "LUYEN_TAP",
    "VAN_DUNG",
}


VALID_STATUSES = {
    "draft",
    "approved",
    "deprecated",
}


@dataclass
class LearningActivity:
    """
    Một hoạt động học trong tiến trình dạy học.

    Đây là model semantic:
    - lưu ý nghĩa sư phạm;
    - không quy định bảng/cột;
    - không quy định tên cột;
    - không quy định định dạng Word/PDF.

    Cấu trúc semantic của hoạt động:

    a) Mục tiêu
    b) Nội dung
    c) Sản phẩm
    d) Tổ chức thực hiện

    Ngoài ra:
    - teacher_conclusion lưu nội dung GV chốt;
    - content_sections dùng cho các đơn vị nội dung nhỏ;
    - resource_ids liên kết tới học liệu/hình ảnh.
    """

    activity_id: str
    lesson_key: str
    period_in_lesson: int | None
    activity_type: str
    title: str

    # ---------------------------------------------------------
    # Truy vết
    # ---------------------------------------------------------

    objective_ids: list[str] = field(
        default_factory=list
    )

    yccd_ids: list[str] = field(
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
    # Đề mục / đơn vị nội dung nhỏ
    #
    # Đặc biệt hữu ích với HINH_THANH_KIEN_THUC:
    #
    # Hoạt động 2. Hình thành kiến thức
    #   1. Đề mục SGK
    #   2. Đề mục SGK
    #
    # Quy tắc nghiệp vụ cụ thể sẽ được kiểm tra
    # ở tầng cấu trúc cao hơn.
    # ---------------------------------------------------------

    content_sections: list[
        ContentSection
    ] = field(
        default_factory=list
    )

    # ---------------------------------------------------------
    # Học liệu / tài nguyên trực quan
    #
    # Chỉ lưu ID liên kết.
    # Không chứa logic tìm ảnh, tạo ảnh hay trình bày ảnh.
    # ---------------------------------------------------------

    resource_ids: list[str] = field(
        default_factory=list
    )

    # ---------------------------------------------------------
    # Nội dung giáo viên chốt sau hoạt động
    # ---------------------------------------------------------

    teacher_conclusion: str = ""

    order: int = 1
    status: str = "draft"

    def validate(self) -> None:
        # -----------------------------------------------------
        # 1. ACTIVITY_ID
        # -----------------------------------------------------

        if not self._clean_text(
            self.activity_id
        ):
            raise ValueError(
                "ACTIVITY_ID không được để trống."
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
        # 3. PERIOD_IN_LESSON
        #
        # None vẫn được phép ở model thấp.
        # Tầng Period/Lesson sẽ quyết định trường hợp
        # nào bắt buộc phải có số tiết.
        # -----------------------------------------------------

        if self.period_in_lesson is not None:
            try:
                period_number = int(
                    self.period_in_lesson
                )
            except (
                TypeError,
                ValueError,
            ) as error:
                raise ValueError(
                    "PERIOD_IN_LESSON phải là số nguyên."
                ) from error

            if period_number <= 0:
                raise ValueError(
                    "PERIOD_IN_LESSON phải lớn hơn 0."
                )

        # -----------------------------------------------------
        # 4. ACTIVITY_TYPE
        # -----------------------------------------------------

        if (
            self.normalized_type
            not in VALID_ACTIVITY_TYPES
        ):
            raise ValueError(
                "ACTIVITY_TYPE không hợp lệ: "
                f"{self.activity_type}"
            )

        # -----------------------------------------------------
        # 5. TITLE
        # -----------------------------------------------------

        if not self._clean_text(
            self.title
        ):
            raise ValueError(
                "TITLE không được để trống."
            )

        # -----------------------------------------------------
        # 6. OBJECTIVE_IDS
        # -----------------------------------------------------

        self._validate_id_list(
            self.objective_ids,
            "OBJECTIVE_IDS",
        )

        # -----------------------------------------------------
        # 7. YCCD_IDS
        # -----------------------------------------------------

        self._validate_id_list(
            self.yccd_ids,
            "YCCD_IDS",
        )

        # -----------------------------------------------------
        # 8. RESOURCE_IDS
        # -----------------------------------------------------

        self._validate_id_list(
            self.resource_ids,
            "RESOURCE_IDS",
        )

        # -----------------------------------------------------
        # 9. IMPLEMENTATION_STEPS
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
                    "STEP_ID bị trùng trong activity: "
                    f"{step.step_id}"
                )

            step_ids.add(
                step.step_id
            )

            step_order = int(
                step.step_order
            )

            if step_order in step_orders:
                raise ValueError(
                    "STEP_ORDER bị trùng "
                    "trong activity: "
                    f"{step_order}"
                )

            step_orders.add(
                step_order
            )

        # -----------------------------------------------------
        # 10. CONTENT_SECTIONS
        # -----------------------------------------------------

        section_ids: set[str] = set()
        section_orders: set[int] = set()

        for section in self.content_sections:
            if not isinstance(
                section,
                ContentSection,
            ):
                raise ValueError(
                    "CONTENT_SECTIONS chỉ được "
                    "chứa ContentSection."
                )

            section.validate()

            if (
                section.lesson_key
                != self.lesson_key
            ):
                raise ValueError(
                    "ContentSection không cùng "
                    "LESSON_KEY với activity."
                )

            if (
                section.section_id
                in section_ids
            ):
                raise ValueError(
                    "SECTION_ID bị trùng "
                    "trong activity: "
                    f"{section.section_id}"
                )

            section_ids.add(
                section.section_id
            )

            section_order = int(
                section.section_order
            )

            if (
                section_order
                in section_orders
            ):
                raise ValueError(
                    "SECTION_ORDER bị trùng "
                    "trong activity: "
                    f"{section_order}"
                )

            section_orders.add(
                section_order
            )

        # -----------------------------------------------------
        # 11. ORDER
        # -----------------------------------------------------

        try:
            activity_order = int(
                self.order
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "ORDER phải là số nguyên."
            ) from error

        if activity_order <= 0:
            raise ValueError(
                "ORDER phải lớn hơn 0."
            )

        # -----------------------------------------------------
        # 12. TEACHER_CONCLUSION
        #
        # Theo nguyên tắc đã chốt:
        # sau mỗi hoạt động GV cần chốt lại nội dung
        # quan trọng của hoạt động.
        # -----------------------------------------------------

        if not self._clean_text(
            self.teacher_conclusion
        ):
            raise ValueError(
                "TEACHER_CONCLUSION không được "
                "để trống."
            )

        # -----------------------------------------------------
        # 13. STATUS
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
    def normalized_type(
        self,
    ) -> str:
        return (
            self._clean_text(
                self.activity_type
            ).upper()
        )

    def get_implementation_steps(
        self,
    ) -> list[ImplementationStep]:
        """
        Trả về các bước tổ chức thực hiện
        theo STEP_ORDER.
        """

        self.validate()

        return sorted(
            self.implementation_steps,
            key=lambda item: int(
                item.step_order
            ),
        )

    def get_content_sections(
        self,
    ) -> list[ContentSection]:
        """
        Trả về các đề mục nội dung
        theo SECTION_ORDER.
        """

        self.validate()

        return sorted(
            self.content_sections,
            key=lambda item: int(
                item.section_order
            ),
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        self.validate()

        return {
            "ACTIVITY_ID": (
                self.activity_id
            ),
            "LESSON_KEY": (
                self.lesson_key
            ),
            "PERIOD_IN_LESSON": (
                None
                if self.period_in_lesson is None
                else int(
                    self.period_in_lesson
                )
            ),
            "ACTIVITY_TYPE": (
                self.normalized_type
            ),
            "TITLE": (
                self.title
            ),
            "OBJECTIVE_IDS": list(
                self.objective_ids
            ),
            "YCCD_IDS": list(
                self.yccd_ids
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
            "CONTENT_SECTIONS": [
                section.to_dict()
                for section
                in self.get_content_sections()
            ],
            "RESOURCE_IDS": list(
                self.resource_ids
            ),
            "TEACHER_CONCLUSION": (
                self.teacher_conclusion
            ),
            "ORDER": int(
                self.order
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