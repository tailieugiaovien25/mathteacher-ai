from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


VALID_ROLES = {
    "CHINH",
    "CUNG_CO",
    "MO_RONG",
}

VALID_STATUSES = {
    "draft",
    "approved",
    "deprecated",
}


@dataclass
class YCCDPeriodMapRecord:
    """Một quan hệ giữa YCCĐ và tiết trong bài."""

    map_id: str
    lesson_key: str
    period_in_lesson: int
    yccd_id: str
    role: str
    version: str = "1.0"
    status: str = "draft"
    updated_at: date | datetime | None = None
    note: str | None = None

    def validate(self) -> None:
        if not self._clean_text(
            self.map_id
        ):
            raise ValueError(
                "MAP_ID không được để trống."
            )

        if not self._clean_text(
            self.lesson_key
        ):
            raise ValueError(
                "LESSON_KEY không được để trống."
            )

        if not self._clean_text(
            self.yccd_id
        ):
            raise ValueError(
                "YCCD_ID không được để trống."
            )

        try:
            period_number = int(
                self.period_in_lesson
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "TIET_TRONG_BAI phải là số nguyên."
            ) from error

        if period_number <= 0:
            raise ValueError(
                "TIET_TRONG_BAI phải lớn hơn 0."
            )

        normalized_role = (
            self._clean_text(
                self.role
            ).upper()
        )

        if normalized_role not in VALID_ROLES:
            raise ValueError(
                "VAI_TRO không hợp lệ: "
                f"{self.role}"
            )

        normalized_status = (
            self._clean_text(
                self.status
            ).lower()
        )

        if normalized_status not in VALID_STATUSES:
            raise ValueError(
                "TRANG_THAI không hợp lệ: "
                f"{self.status}"
            )

    def to_excel_row(
        self,
    ) -> dict[str, Any]:
        self.validate()

        return {
            "MAP_ID": self.map_id,
            "LESSON_KEY": self.lesson_key,
            "TIET_TRONG_BAI": int(
                self.period_in_lesson
            ),
            "YCCD_ID": self.yccd_id,
            "VAI_TRO": (
                self.role.upper()
            ),
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