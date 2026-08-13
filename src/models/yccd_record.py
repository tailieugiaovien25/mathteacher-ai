from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


VALID_STATUSES = {
    "draft",
    "approved",
    "deprecated",
}

VALID_YCCD_TYPES = {
    "CHINH_THUC",
    "TRIEN_KHAI",
}


@dataclass
class YCCDRecord:
    """Mô hình dữ liệu chuẩn cho một Yêu cầu cần đạt."""

    yccd_id: str
    lesson_key: str
    subject: str
    grade: int | str
    lesson_id: str | None
    lesson_name: str
    order: int
    requirement: str

    yccd_type: str = "TRIEN_KHAI"
    source_yccd_id: str | None = None

    source: str | None = None
    reference: str | None = None
    version: str = "1.0"
    status: str = "draft"
    updated_at: date | datetime | None = None
    note: str | None = None

    def validate(self) -> None:
        """Kiểm tra tính hợp lệ của bản ghi YCCĐ."""

        if not self._clean_text(
            self.yccd_id
        ):
            raise ValueError(
                "YCCD_ID không được để trống."
            )

        if not self._clean_text(
            self.lesson_key
        ):
            raise ValueError(
                "LESSON_KEY không được để trống."
            )

        if not self._clean_text(
            self.subject
        ):
            raise ValueError(
                "MON không được để trống."
            )

        if not self._clean_text(
            self.lesson_name
        ):
            raise ValueError(
                "TEN_BAI không được để trống."
            )

        if not self._clean_text(
            self.requirement
        ):
            raise ValueError(
                "YEU_CAU_CAN_DAT không được để trống."
            )

        try:
            order_number = int(
                self.order
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "YCCD_ORDER phải là số nguyên."
            ) from error

        if order_number <= 0:
            raise ValueError(
                "YCCD_ORDER phải lớn hơn 0."
            )

        normalized_type = (
            self._clean_text(
                self.yccd_type
            ).upper()
        )

        if (
            normalized_type
            not in VALID_YCCD_TYPES
        ):
            raise ValueError(
                "LOAI_YCCD không hợp lệ: "
                f"{self.yccd_type}"
            )

        normalized_source_id = (
            self._clean_text(
                self.source_yccd_id
            )
        )

        if (
            normalized_type
            == "CHINH_THUC"
            and normalized_source_id
        ):
            raise ValueError(
                "YCCĐ CHINH_THUC không được "
                "có YCCD_GOC_ID."
            )

        if (
            normalized_type
            == "TRIEN_KHAI"
            and not normalized_source_id
        ):
            raise ValueError(
                "YCCĐ TRIEN_KHAI phải có "
                "YCCD_GOC_ID."
            )

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
                "TRANG_THAI không hợp lệ: "
                f"{self.status}"
            )

    def to_excel_row(
        self,
    ) -> dict[str, Any]:
        """Chuyển model sang cấu trúc cột của tblYCCD."""

        self.validate()

        return {
            "YCCD_ID": self.yccd_id,
            "LESSON_KEY": self.lesson_key,
            "MON": self.subject,
            "KHOI": self.grade,
            "BAI_ID": self.lesson_id,
            "TEN_BAI": self.lesson_name,
            "YCCD_ORDER": int(
                self.order
            ),
            "YEU_CAU_CAN_DAT": (
                self.requirement
            ),
            "LOAI_YCCD": (
                self.yccd_type.upper()
            ),
            "YCCD_GOC_ID": (
                self.source_yccd_id
            ),
            "NGUON": self.source,
            "THAM_CHIEU": self.reference,
            "PHIEN_BAN": self.version,
            "TRANG_THAI": (
                self.status.lower()
            ),
            "NGAY_CAP_NHAT": (
                self.updated_at
            ),
            "GHI_CHU": self.note,
        }

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return " ".join(
            str(value).strip().split()
        )