from dataclasses import dataclass, field
from typing import Any

from models.learning_activity import LearningActivity


# ============================================================
# CHẾ ĐỘ GIÁO ÁN
# ============================================================

VALID_PLAN_MODES = {
    "FULL_LESSON",
    "SINGLE_PERIOD",
}


# ============================================================
# LOẠI BÀI / TIẾT
# ============================================================

VALID_LESSON_TYPES = {
    "LY_THUYET",
    "LUYEN_TAP",
    "ON_TAP",
}


# ============================================================
# TRẠNG THÁI
# ============================================================

VALID_STATUSES = {
    "draft",
    "approved",
    "deprecated",
}


@dataclass
class LessonPlanStructure:
    """
    Cấu trúc một giáo án.

    PLAN_MODE:

    FULL_LESSON
        Một giáo án cho toàn bộ bài.
        Có thể gồm nhiều tiết.

    SINGLE_PERIOD
        Một giáo án độc lập cho một tiết.

    LESSON_TYPE:

    LY_THUYET
        Có đủ:
        - MO_DAU
        - HINH_THANH_KIEN_THUC
        - LUYEN_TAP
        - VAN_DUNG

    LUYEN_TAP
        Không bắt buộc HINH_THANH_KIEN_THUC.

    ON_TAP
        Không bắt buộc HINH_THANH_KIEN_THUC.
        MO_DAU có thể mang tên:
        - Nhắc lại kiến thức
        - Hệ thống kiến thức
        - Khởi động
        - ...
    """

    plan_id: str
    lesson_key: str
    plan_mode: str
    lesson_type: str

    total_periods: int

    period_in_lesson: int | None = None

    activities: list[LearningActivity] = field(
        default_factory=list
    )

    status: str = "draft"

    def validate(self) -> None:
        # ----------------------------------------------------
        # 1. PLAN_ID
        # ----------------------------------------------------

        if not self._clean_text(
            self.plan_id
        ):
            raise ValueError(
                "PLAN_ID không được để trống."
            )

        # ----------------------------------------------------
        # 2. LESSON_KEY
        # ----------------------------------------------------

        if not self._clean_text(
            self.lesson_key
        ):
            raise ValueError(
                "LESSON_KEY không được để trống."
            )

        # ----------------------------------------------------
        # 3. PLAN_MODE
        # ----------------------------------------------------

        mode = self.normalized_plan_mode

        if mode not in VALID_PLAN_MODES:
            raise ValueError(
                "PLAN_MODE không hợp lệ: "
                f"{self.plan_mode}"
            )

        # ----------------------------------------------------
        # 4. LESSON_TYPE
        # ----------------------------------------------------

        lesson_type = (
            self.normalized_lesson_type
        )

        if (
            lesson_type
            not in VALID_LESSON_TYPES
        ):
            raise ValueError(
                "LESSON_TYPE không hợp lệ: "
                f"{self.lesson_type}"
            )

        # ----------------------------------------------------
        # 5. TOTAL_PERIODS
        # ----------------------------------------------------

        try:
            total_periods = int(
                self.total_periods
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "TOTAL_PERIODS phải là số nguyên."
            ) from error

        if total_periods <= 0:
            raise ValueError(
                "TOTAL_PERIODS phải lớn hơn 0."
            )

        # ----------------------------------------------------
        # 6. QUY TẮC PLAN_MODE
        # ----------------------------------------------------

        if mode == "FULL_LESSON":
            if self.period_in_lesson is not None:
                raise ValueError(
                    "FULL_LESSON không được gắn "
                    "PERIOD_IN_LESSON cụ thể."
                )

        elif mode == "SINGLE_PERIOD":
            if self.period_in_lesson is None:
                raise ValueError(
                    "SINGLE_PERIOD bắt buộc phải có "
                    "PERIOD_IN_LESSON."
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
                    "PERIOD_IN_LESSON phải là "
                    "số nguyên."
                ) from error

            if period_number <= 0:
                raise ValueError(
                    "PERIOD_IN_LESSON phải "
                    "lớn hơn 0."
                )

            if period_number > total_periods:
                raise ValueError(
                    "PERIOD_IN_LESSON không được "
                    "lớn hơn TOTAL_PERIODS."
                )

        # ----------------------------------------------------
        # 7. KIỂM TRA TỪNG ACTIVITY
        # ----------------------------------------------------

        activity_ids: list[str] = []

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

            # Hoạt động phải cùng bài
            if (
                activity.lesson_key
                != self.lesson_key
            ):
                raise ValueError(
                    "Hoạt động không cùng "
                    "LESSON_KEY với giáo án."
                )

            # Không được trùng ACTIVITY_ID
            if (
                activity.activity_id
                in activity_ids
            ):
                raise ValueError(
                    "ACTIVITY_ID bị trùng: "
                    f"{activity.activity_id}"
                )

            activity_ids.append(
                activity.activity_id
            )

            # -----------------------------------------------
            # FULL_LESSON
            # -----------------------------------------------

            if mode == "FULL_LESSON":
                if (
                    activity.period_in_lesson
                    is None
                ):
                    raise ValueError(
                        "Hoạt động trong FULL_LESSON "
                        "phải thuộc một tiết cụ thể."
                    )

                activity_period = int(
                    activity.period_in_lesson
                )

                if (
                    activity_period
                    > total_periods
                ):
                    raise ValueError(
                        "Hoạt động thuộc tiết vượt quá "
                        "TOTAL_PERIODS."
                    )

            # -----------------------------------------------
            # SINGLE_PERIOD
            # -----------------------------------------------

            elif mode == "SINGLE_PERIOD":
                if (
                    activity.period_in_lesson
                    != self.period_in_lesson
                ):
                    raise ValueError(
                        "SINGLE_PERIOD chứa hoạt động "
                        "của tiết khác."
                    )

        # ----------------------------------------------------
        # 8. ORDER KHÔNG ĐƯỢC TRÙNG TRONG CÙNG TIẾT
        # ----------------------------------------------------

        period_orders: dict[
            int,
            set[int],
        ] = {}

        for activity in self.activities:
            if (
                activity.period_in_lesson
                is None
            ):
                continue

            period = int(
                activity.period_in_lesson
            )

            order = int(
                activity.order
            )

            if period not in period_orders:
                period_orders[period] = set()

            if order in period_orders[period]:
                raise ValueError(
                    "ORDER bị trùng trong tiết "
                    f"{period}: {order}"
                )

            period_orders[period].add(
                order
            )

        # ----------------------------------------------------
        # 9. STATUS
        # ----------------------------------------------------

        status = (
            self._clean_text(
                self.status
            ).lower()
        )

        if status not in VALID_STATUSES:
            raise ValueError(
                "STATUS không hợp lệ: "
                f"{self.status}"
            )

    @property
    def normalized_plan_mode(
        self,
    ) -> str:
        return (
            self._clean_text(
                self.plan_mode
            ).upper()
        )

    @property
    def normalized_lesson_type(
        self,
    ) -> str:
        return (
            self._clean_text(
                self.lesson_type
            ).upper()
        )

    def get_period_activities(
        self,
        period: int,
    ) -> list[LearningActivity]:
        """
        Lấy các hoạt động của một tiết,
        sắp xếp theo ORDER.
        """

        self.validate()

        try:
            period_number = int(period)
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "PERIOD phải là số nguyên."
            ) from error

        if (
            period_number <= 0
            or period_number
            > int(self.total_periods)
        ):
            raise ValueError(
                "PERIOD nằm ngoài phạm vi bài học."
            )

        result = [
            activity
            for activity in self.activities
            if (
                activity.period_in_lesson
                == period_number
            )
        ]

        return sorted(
            result,
            key=lambda item: int(
                item.order
            ),
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        self.validate()

        return {
            "PLAN_ID": self.plan_id,
            "LESSON_KEY": self.lesson_key,
            "PLAN_MODE": (
                self.normalized_plan_mode
            ),
            "LESSON_TYPE": (
                self.normalized_lesson_type
            ),
            "TOTAL_PERIODS": int(
                self.total_periods
            ),
            "PERIOD_IN_LESSON": (
                self.period_in_lesson
            ),
            "ACTIVITIES": [
                activity.to_dict()
                for activity in self.activities
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