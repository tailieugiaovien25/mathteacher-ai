from dataclasses import dataclass
from typing import Any


VALID_RESOURCE_TYPES = {
    "EQUIPMENT",
    "IMAGE",
    "GEOMETRY_FIGURE",
    "GRAPH",
    "CHART",
    "DIAGRAM",
    "DOCUMENT",
    "OTHER",
}


VALID_SOURCE_TYPES = {
    "GENERATED",
    "WEB",
    "TEACHER_UPLOAD",
    "LOCAL",
    "OTHER",
}


VALID_STATUSES = {
    "draft",
    "approved",
    "deprecated",
}


@dataclass
class LearningResource:
    """
    Một thiết bị, học liệu hoặc tài nguyên
    phục vụ dạy học.

    Đây là model semantic.

    Model KHÔNG quy định:
    - tài nguyên nằm ở vị trí nào;
    - kích thước hình ảnh;
    - số cột;
    - bảng;
    - căn lề;
    - font;
    - cách trình bày Word/PDF.

    Những nội dung đó thuộc Template.
    """

    resource_id: str
    resource_type: str
    title: str

    description: str = ""

    source_type: str = "OTHER"
    source_reference: str = ""

    pedagogical_purpose: str = ""
    alt_text: str = ""

    license_info: str = ""
    note: str = ""

    status: str = "draft"

    def validate(self) -> None:
        # -----------------------------------------------------
        # 1. RESOURCE_ID
        # -----------------------------------------------------

        if not self._clean_text(
            self.resource_id
        ):
            raise ValueError(
                "RESOURCE_ID không được để trống."
            )

        # -----------------------------------------------------
        # 2. RESOURCE_TYPE
        # -----------------------------------------------------

        normalized_resource_type = (
            self.normalized_resource_type
        )

        if (
            normalized_resource_type
            not in VALID_RESOURCE_TYPES
        ):
            raise ValueError(
                "RESOURCE_TYPE không hợp lệ: "
                f"{self.resource_type}"
            )

        # -----------------------------------------------------
        # 3. TITLE
        # -----------------------------------------------------

        if not self._clean_text(
            self.title
        ):
            raise ValueError(
                "TITLE không được để trống."
            )

        # -----------------------------------------------------
        # 4. SOURCE_TYPE
        # -----------------------------------------------------

        normalized_source_type = (
            self.normalized_source_type
        )

        if (
            normalized_source_type
            not in VALID_SOURCE_TYPES
        ):
            raise ValueError(
                "SOURCE_TYPE không hợp lệ: "
                f"{self.source_type}"
            )

        # -----------------------------------------------------
        # 5. WEB PHẢI CÓ SOURCE_REFERENCE
        # -----------------------------------------------------

        if (
            normalized_source_type
            == "WEB"
            and not self._clean_text(
                self.source_reference
            )
        ):
            raise ValueError(
                "Tài nguyên nguồn WEB bắt buộc "
                "phải có SOURCE_REFERENCE."
            )

        # -----------------------------------------------------
        # 6. TEACHER_UPLOAD / LOCAL
        #
        # Chưa bắt buộc đường dẫn ở tầng model.
        # Sau này Resource Manager sẽ kiểm tra
        # file thực tế.
        # -----------------------------------------------------

        # -----------------------------------------------------
        # 7. ALT_TEXT
        #
        # Với tài nguyên trực quan, alt_text rất hữu ích
        # cho khả năng truy cập và sinh tài liệu.
        #
        # Ở v1.0 ta chưa bắt buộc để tránh làm model
        # quá cứng đối với dữ liệu draft.
        # -----------------------------------------------------

        # -----------------------------------------------------
        # 8. STATUS
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
    def normalized_resource_type(
        self,
    ) -> str:
        return (
            self._clean_text(
                self.resource_type
            ).upper()
        )

    @property
    def normalized_source_type(
        self,
    ) -> str:
        return (
            self._clean_text(
                self.source_type
            ).upper()
        )

    @property
    def is_visual(
        self,
    ) -> bool:
        return (
            self.normalized_resource_type
            in {
                "IMAGE",
                "GEOMETRY_FIGURE",
                "GRAPH",
                "CHART",
                "DIAGRAM",
            }
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        self.validate()

        return {
            "RESOURCE_ID": (
                self.resource_id
            ),
            "RESOURCE_TYPE": (
                self.normalized_resource_type
            ),
            "TITLE": (
                self.title
            ),
            "DESCRIPTION": (
                self.description
            ),
            "SOURCE_TYPE": (
                self.normalized_source_type
            ),
            "SOURCE_REFERENCE": (
                self.source_reference
            ),
            "PEDAGOGICAL_PURPOSE": (
                self.pedagogical_purpose
            ),
            "ALT_TEXT": (
                self.alt_text
            ),
            "LICENSE_INFO": (
                self.license_info
            ),
            "NOTE": (
                self.note
            ),
            "STATUS": (
                self.status.lower()
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