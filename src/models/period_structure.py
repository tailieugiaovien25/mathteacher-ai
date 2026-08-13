from dataclasses import dataclass, field
from typing import Any

from models.learning_activity import (
    LearningActivity,
)


VALID_PERIOD_TYPES = {
    "LY_THUYET",
    "LUYEN_TAP",
    "ON_TAP",
}


VALID_STATUSES = {
    "draft",
    "approved",
    "deprecated",
}


@dataclass
class PeriodStructure:
    """
    Cấu trúc semantic của một tiết học.

    Model này chỉ quản lý logic sư phạm.
    Không chứa:
    - số cột;
    - tên cột;
    - bảng;
    - font;
    - bố cục Word/PDF.

    PERIOD_TYPE:

    LY_THUYET
        Bắt buộc có:
        - MO_DAU
        - HINH_THANH_KIEN_THUC
        - LUYEN_TAP
        - VAN_DUNG

    LUYEN_TAP
        Bắt buộc có:
        - MO_DAU
        - LUYEN_TAP
        - VAN_DUNG

        HINH_THANH_KIEN_THUC là tùy chọn.

    ON_TAP
        Bắt buộc có:
        - MO_DAU
        - LUYEN_TAP
        - VAN_DUNG

        HINH_THANH_KIEN_THUC là tùy chọn.

        MO_DAU có thể mang tên:
        - Nhắc lại kiến thức
        - Hệ thống kiến thức
        - Sơ đồ hóa kiến thức
        - ...
    """

    lesson_key: str
    period_in_lesson: int
    period_type: str

    activities: list[
        LearningActivity
    ] = field(
        default_factory=list
    )

    status: str = "draft"

    def validate(self) -> None:
        # -----------------------------------------------------
        # 1. LESSON_KEY
        # -----------------------------------------------------

        if not self._clean_text(
            self.lesson_key
        ):
            raise ValueError(
                "LESSON_KEY không được để trống."
            )

        # -----------------------------------------------------
        # 2. PERIOD_IN_LESSON
        # -----------------------------------------------------

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
        # 3. PERIOD_TYPE
        # -----------------------------------------------------

        period_type = (
            self.normalized_period_type
        )

        if (
            period_type
            not in VALID_PERIOD_TYPES
        ):
            raise ValueError(
                "PERIOD_TYPE không hợp lệ: "
                f"{self.period_type}"
            )

        # -----------------------------------------------------
        # 4. STATUS
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

        # -----------------------------------------------------
        # 5. PHẢI CÓ HOẠT ĐỘNG
        # -----------------------------------------------------

        if not self.activities:
            raise ValueError(
                "Một tiết học phải có ít nhất "
                "một LearningActivity."
            )

        # -----------------------------------------------------
        # 6. KIỂM TRA TỪNG ACTIVITY
        # -----------------------------------------------------

        activity_ids: set[str] = set()
        activity_orders: set[int] = set()

        for activity in self.activities:
            if not isinstance(
                activity,
                LearningActivity,
            ):
                raise ValueError(
                    "ACTIVITIES chỉ được chứa "
                    "LearningActivity."
                )

            activity.validate()

            # Cùng bài.
            if (
                activity.lesson_key
                != self.lesson_key
            ):
                raise ValueError(
                    "LearningActivity không cùng "
                    "LESSON_KEY với PeriodStructure."
                )

            # Đúng tiết.
            if (
                activity.period_in_lesson
                != period_number
            ):
                raise ValueError(
                    "LearningActivity không thuộc đúng "
                    "PERIOD_IN_LESSON."
                )

            # Không trùng ID.
            if (
                activity.activity_id
                in activity_ids
            ):
                raise ValueError(
                    "ACTIVITY_ID bị trùng trong tiết: "
                    f"{activity.activity_id}"
                )

            activity_ids.add(
                activity.activity_id
            )

            # Không trùng thứ tự.
            activity_order = int(
                activity.order
            )

            if (
                activity_order
                in activity_orders
            ):
                raise ValueError(
                    "ORDER bị trùng trong tiết: "
                    f"{activity_order}"
                )

            activity_orders.add(
                activity_order
            )

        # -----------------------------------------------------
        # 7. LẤY CÁC LOẠI HOẠT ĐỘNG HIỆN CÓ
        # -----------------------------------------------------

        activity_types = {
            activity.normalized_type
            for activity
            in self.activities
        }

        # -----------------------------------------------------
        # 8. MO_DAU LUÔN BẮT BUỘC
        # -----------------------------------------------------

        if (
            "MO_DAU"
            not in activity_types
        ):
            raise ValueError(
                "Tiết học bắt buộc phải có MO_DAU."
            )

        # -----------------------------------------------------
        # 9. LUYEN_TAP LUÔN BẮT BUỘC
        # -----------------------------------------------------

        if (
            "LUYEN_TAP"
            not in activity_types
        ):
            raise ValueError(
                "Tiết học bắt buộc phải có LUYEN_TAP."
            )

        # -----------------------------------------------------
        # 10. VAN_DUNG LUÔN BẮT BUỘC
        # -----------------------------------------------------

        if (
            "VAN_DUNG"
            not in activity_types
        ):
            raise ValueError(
                "Tiết học bắt buộc phải có VAN_DUNG."
            )

        # -----------------------------------------------------
        # 11. LY_THUYET BẮT BUỘC CÓ
        # HINH_THANH_KIEN_THUC
        # -----------------------------------------------------

        if (
            period_type
            == "LY_THUYET"
        ):
            if (
                "HINH_THANH_KIEN_THUC"
                not in activity_types
            ):
                raise ValueError(
                    "Tiết LY_THUYET bắt buộc "
                    "phải có "
                    "HINH_THANH_KIEN_THUC."
                )

        # -----------------------------------------------------
        # 12. CONTENT SECTION TRONG HÌNH THÀNH KIẾN THỨC
        #
        # LearningActivity đã tự kiểm tra:
        # - SECTION_ID không trùng;
        # - SECTION_ORDER không trùng;
        # - SECTION cùng LESSON_KEY.
        #
        # Ở đây không bắt buộc activity HINH_THANH_KIEN_THUC
        # phải có ContentSection vì:
        # - dữ liệu có thể đang ở trạng thái draft;
        # - một số nội dung đơn giản có thể chưa cần chia mục;
        # - quy tắc bám SGK có thể được kiểm tra ở tầng
        #   LessonPlan semantic / builder sau này.
        # -----------------------------------------------------

    @property
    def normalized_period_type(
        self,
    ) -> str:
        return (
            self._clean_text(
                self.period_type
            ).upper()
        )

    def get_activities(
        self,
    ) -> list[LearningActivity]:
        """
        Trả về toàn bộ hoạt động
        theo đúng ORDER.
        """

        self.validate()

        return sorted(
            self.activities,
            key=lambda item: int(
                item.order
            ),
        )

    def get_activities_by_type(
        self,
        activity_type: str,
    ) -> list[LearningActivity]:
        """
        Lấy các hoạt động theo loại.

        Một ACTIVITY_TYPE được phép
        xuất hiện nhiều lần trong một tiết.
        """

        self.validate()

        normalized_type = (
            self._clean_text(
                activity_type
            ).upper()
        )

        return [
            activity
            for activity
            in self.get_activities()
            if (
                activity.normalized_type
                == normalized_type
            )
        ]

    def to_dict(
        self,
    ) -> dict[str, Any]:
        self.validate()

        return {
            "LESSON_KEY": (
                self.lesson_key
            ),
            "PERIOD_IN_LESSON": int(
                self.period_in_lesson
            ),
            "PERIOD_TYPE": (
                self.normalized_period_type
            ),
            "ACTIVITIES": [
                activity.to_dict()
                for activity
                in self.get_activities()
            ],
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