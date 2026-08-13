from dataclasses import dataclass, field
from typing import Any

from models.lesson_objective import LessonObjective
from models.learning_resource import LearningResource
from models.period_structure import PeriodStructure


VALID_PLAN_MODES = {
    "FULL_LESSON",
    "SINGLE_PERIOD",
}


VALID_STATUSES = {
    "draft",
    "approved",
    "deprecated",
}


@dataclass
class LessonPlanSemantic:
    """
    Giáo án hoàn chỉnh ở tầng logic/semantic.

    Model này không chứa bất kỳ logic trình bày nào:
    - không số cột;
    - không tên cột;
    - không bảng;
    - không font;
    - không căn lề;
    - không bố cục Word/PDF.

    Hai chế độ:

    FULL_LESSON
        Một giáo án cho toàn bộ bài,
        có thể gồm nhiều tiết.

    SINGLE_PERIOD
        Một giáo án độc lập cho một tiết.
    """

    plan_id: str
    lesson_key: str
    plan_mode: str
    total_periods: int

    period_in_lesson: int | None = None

    objectives: list[
        LessonObjective
    ] = field(
        default_factory=list
    )

    resources: list[
        LearningResource
    ] = field(
        default_factory=list
    )

    periods: list[
        PeriodStructure
    ] = field(
        default_factory=list
    )

    status: str = "draft"

    def validate(self) -> None:
        # -----------------------------------------------------
        # 1. PLAN_ID
        # -----------------------------------------------------

        if not self._clean_text(
            self.plan_id
        ):
            raise ValueError(
                "PLAN_ID không được để trống."
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
        # 3. PLAN_MODE
        # -----------------------------------------------------

        mode = (
            self.normalized_plan_mode
        )

        if mode not in VALID_PLAN_MODES:
            raise ValueError(
                "PLAN_MODE không hợp lệ: "
                f"{self.plan_mode}"
            )

        # -----------------------------------------------------
        # 4. TOTAL_PERIODS
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # 5. QUY TẮC MODE
        # -----------------------------------------------------

        if mode == "FULL_LESSON":
            if (
                self.period_in_lesson
                is not None
            ):
                raise ValueError(
                    "FULL_LESSON không được có "
                    "PERIOD_IN_LESSON cụ thể."
                )

        elif mode == "SINGLE_PERIOD":
            if (
                self.period_in_lesson
                is None
            ):
                raise ValueError(
                    "SINGLE_PERIOD bắt buộc phải có "
                    "PERIOD_IN_LESSON."
                )

            try:
                selected_period = int(
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

            if selected_period <= 0:
                raise ValueError(
                    "PERIOD_IN_LESSON phải "
                    "lớn hơn 0."
                )

            if selected_period > total_periods:
                raise ValueError(
                    "PERIOD_IN_LESSON không được "
                    "lớn hơn TOTAL_PERIODS."
                )

        # -----------------------------------------------------
        # 6. OBJECTIVES
        # -----------------------------------------------------

        objective_ids: set[str] = set()

        for objective in self.objectives:
            if not isinstance(
                objective,
                LessonObjective,
            ):
                raise ValueError(
                    "OBJECTIVES chỉ được chứa "
                    "LessonObjective."
                )

            objective.validate()

            if (
                objective.lesson_key
                != self.lesson_key
            ):
                raise ValueError(
                    "LessonObjective không cùng "
                    "LESSON_KEY với giáo án."
                )

            if (
                objective.objective_id
                in objective_ids
            ):
                raise ValueError(
                    "OBJECTIVE_ID bị trùng: "
                    f"{objective.objective_id}"
                )

            objective_ids.add(
                objective.objective_id
            )

        # -----------------------------------------------------
        # 7. RESOURCES
        # -----------------------------------------------------

        resource_ids: set[str] = set()

        for resource in self.resources:
            if not isinstance(
                resource,
                LearningResource,
            ):
                raise ValueError(
                    "RESOURCES chỉ được chứa "
                    "LearningResource."
                )

            resource.validate()

            if (
                resource.resource_id
                in resource_ids
            ):
                raise ValueError(
                    "RESOURCE_ID bị trùng: "
                    f"{resource.resource_id}"
                )

            resource_ids.add(
                resource.resource_id
            )

        # -----------------------------------------------------
        # 8. PERIODS
        # -----------------------------------------------------

        if not self.periods:
            raise ValueError(
                "Giáo án phải có ít nhất "
                "một PeriodStructure."
            )

        period_numbers: set[int] = set()

        for period in self.periods:
            if not isinstance(
                period,
                PeriodStructure,
            ):
                raise ValueError(
                    "PERIODS chỉ được chứa "
                    "PeriodStructure."
                )

            period.validate()

            if (
                period.lesson_key
                != self.lesson_key
            ):
                raise ValueError(
                    "PeriodStructure không cùng "
                    "LESSON_KEY với giáo án."
                )

            period_number = int(
                period.period_in_lesson
            )

            if (
                period_number
                > total_periods
            ):
                raise ValueError(
                    "PeriodStructure vượt quá "
                    "TOTAL_PERIODS."
                )

            if (
                period_number
                in period_numbers
            ):
                raise ValueError(
                    "Trùng PERIOD_IN_LESSON: "
                    f"{period_number}"
                )

            period_numbers.add(
                period_number
            )

        # -----------------------------------------------------
        # 9. FULL_LESSON
        #
        # Không bắt buộc phải đủ toàn bộ số tiết ở trạng thái
        # draft, vì giáo án có thể đang được xây từng phần.
        # -----------------------------------------------------

        # -----------------------------------------------------
        # 10. SINGLE_PERIOD
        # -----------------------------------------------------

        if mode == "SINGLE_PERIOD":
            if len(self.periods) != 1:
                raise ValueError(
                    "SINGLE_PERIOD phải chứa "
                    "đúng một PeriodStructure."
                )

            only_period = self.periods[0]

            if (
                int(
                    only_period.period_in_lesson
                )
                != int(
                    self.period_in_lesson
                )
            ):
                raise ValueError(
                    "PeriodStructure không khớp "
                    "PERIOD_IN_LESSON của giáo án."
                )

        # -----------------------------------------------------
        # 11. KIỂM TRA THAM CHIẾU TRONG ACTIVITY
        # -----------------------------------------------------

        for period in self.periods:
            for activity in period.activities:
                # ---------------------------------------------
                # OBJECTIVE_IDS phải tồn tại trong plan
                # ---------------------------------------------

                for objective_id in (
                    activity.objective_ids
                ):
                    if (
                        objective_id
                        not in objective_ids
                    ):
                        raise ValueError(
                            "Activity tham chiếu "
                            "OBJECTIVE_ID không tồn tại: "
                            f"{objective_id}"
                        )

                # ---------------------------------------------
                # RESOURCE_IDS phải tồn tại trong plan
                # ---------------------------------------------

                for resource_id in (
                    activity.resource_ids
                ):
                    if (
                        resource_id
                        not in resource_ids
                    ):
                        raise ValueError(
                            "Activity tham chiếu "
                            "RESOURCE_ID không tồn tại: "
                            f"{resource_id}"
                        )

                # ---------------------------------------------
                # CONTENT SECTION
                # ---------------------------------------------

                for section in (
                    activity.content_sections
                ):
                    for objective_id in (
                        section.objective_ids
                    ):
                        if (
                            objective_id
                            not in objective_ids
                        ):
                            raise ValueError(
                                "ContentSection tham chiếu "
                                "OBJECTIVE_ID không tồn tại: "
                                f"{objective_id}"
                            )

        # -----------------------------------------------------
        # 12. STATUS
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
    def normalized_plan_mode(
        self,
    ) -> str:
        return (
            self._clean_text(
                self.plan_mode
            ).upper()
        )

    def get_periods(
        self,
    ) -> list[PeriodStructure]:
        """
        Trả về các tiết theo thứ tự.
        """

        self.validate()

        return sorted(
            self.periods,
            key=lambda item: int(
                item.period_in_lesson
            ),
        )

    def get_period(
        self,
        period_in_lesson: int,
    ) -> PeriodStructure:
        """
        Lấy một tiết cụ thể.
        """

        self.validate()

        try:
            period_number = int(
                period_in_lesson
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "PERIOD_IN_LESSON phải là "
                "số nguyên."
            ) from error

        for period in self.periods:
            if (
                int(
                    period.period_in_lesson
                )
                == period_number
            ):
                return period

        raise ValueError(
            "Không tìm thấy PeriodStructure "
            f"cho tiết {period_number}."
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        self.validate()

        return {
            "PLAN_ID": (
                self.plan_id
            ),
            "LESSON_KEY": (
                self.lesson_key
            ),
            "PLAN_MODE": (
                self.normalized_plan_mode
            ),
            "TOTAL_PERIODS": int(
                self.total_periods
            ),
            "PERIOD_IN_LESSON": (
                None
                if self.period_in_lesson is None
                else int(
                    self.period_in_lesson
                )
            ),
            "OBJECTIVES": [
                objective.to_dict()
                for objective
                in self.objectives
            ],
            "RESOURCES": [
                resource.to_dict()
                for resource
                in self.resources
            ],
            "PERIODS": [
                period.to_dict()
                for period
                in self.get_periods()
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