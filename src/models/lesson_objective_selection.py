from dataclasses import dataclass

from models.yccd_record import YCCDRecord


@dataclass
class LessonObjectiveSelection:
    """Kết quả chọn YCCĐ cho một giáo án."""

    lesson_key: str
    mode: str
    period_in_lesson: int | None
    yccd_records: list[YCCDRecord]

    def validate(self) -> None:
        normalized_mode = (
            str(self.mode)
            .strip()
            .upper()
        )

        if normalized_mode not in {
            "LESSON",
            "PERIOD",
        }:
            raise ValueError(
                "mode phải là LESSON hoặc PERIOD."
            )

        if not str(
            self.lesson_key
        ).strip():
            raise ValueError(
                "LESSON_KEY không được để trống."
            )

        if normalized_mode == "LESSON":
            if (
                self.period_in_lesson
                is not None
            ):
                raise ValueError(
                    "Mode LESSON không được "
                    "có period_in_lesson."
                )

        if normalized_mode == "PERIOD":
            if (
                self.period_in_lesson
                is None
            ):
                raise ValueError(
                    "Mode PERIOD bắt buộc "
                    "có period_in_lesson."
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
                    "period_in_lesson "
                    "phải là số nguyên."
                ) from error

            if period_number <= 0:
                raise ValueError(
                    "period_in_lesson "
                    "phải lớn hơn 0."
                )

    @property
    def yccd_ids(
        self,
    ) -> list[str]:
        return [
            record.yccd_id
            for record in self.yccd_records
        ]