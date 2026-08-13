from pathlib import Path

from models.lesson_objective_selection import (
    LessonObjectiveSelection,
)
from models.yccd_record import YCCDRecord
from repositories.yccd_period_map_repository import (
    YCCDPeriodMapRepository,
)
from repositories.yccd_repository_v2 import (
    YCCDRepositoryV2,
)


class LessonObjectiveResolver:
    """
    Chọn YCCĐ phục vụ soạn giáo án.

    Hai chế độ:
    - LESSON: lấy YCCĐ cho toàn bài.
    - PERIOD: lấy YCCĐ cho một tiết trong bài.
    """

    def __init__(self) -> None:
        self.yccd_repository = (
            YCCDRepositoryV2()
        )

        self.period_map_repository = (
            YCCDPeriodMapRepository()
        )

    def get_objectives(
        self,
        file_path: str | Path,
        lesson_key: str,
        mode: str,
        period_in_lesson: int | None = None,
        status: str = "draft",
    ) -> LessonObjectiveSelection:

        normalized_mode = (
            str(mode)
            .strip()
            .upper()
        )

        # -----------------------------------------------------
        # 1. Kiểm tra request trước
        # -----------------------------------------------------

        request = LessonObjectiveSelection(
            lesson_key=lesson_key,
            mode=normalized_mode,
            period_in_lesson=period_in_lesson,
            yccd_records=[],
        )

        request.validate()

        # -----------------------------------------------------
        # 2. Đọc toàn bộ YCCĐ của bài
        # -----------------------------------------------------

        all_yccd = (
            self.yccd_repository
            .find_by_lesson_key(
                file_path=file_path,
                lesson_key=lesson_key,
                status=status,
            )
        )

        if not all_yccd:
            raise ValueError(
                "Không tìm thấy YCCĐ cho bài: "
                f"{lesson_key}"
            )

        # -----------------------------------------------------
        # 3. MODE = LESSON
        # -----------------------------------------------------

        if normalized_mode == "LESSON":
            selected = (
                self._select_lesson_objectives(
                    all_yccd
                )
            )

            result = LessonObjectiveSelection(
                lesson_key=lesson_key,
                mode="LESSON",
                period_in_lesson=None,
                yccd_records=selected,
            )

            result.validate()

            return result

        # -----------------------------------------------------
        # 4. MODE = PERIOD
        # -----------------------------------------------------

        mappings = (
            self.period_map_repository
            .find_by_period(
                file_path=file_path,
                lesson_key=lesson_key,
                period_in_lesson=(
                    period_in_lesson
                ),
                status=status,
            )
        )

        if not mappings:
            raise ValueError(
                "Không tìm thấy mapping cho "
                f"{lesson_key}, tiết "
                f"{period_in_lesson}."
            )

        yccd_index = {
            record.yccd_id: record
            for record in all_yccd
        }

        selected: list[
            YCCDRecord
        ] = []

        seen_ids: set[str] = set()

        for mapping in mappings:
            yccd_record = yccd_index.get(
                mapping.yccd_id
            )

            if yccd_record is None:
                raise ValueError(
                    "Mapping tham chiếu tới "
                    "YCCD_ID không tồn tại: "
                    f"{mapping.yccd_id}"
                )

            if (
                yccd_record.yccd_id
                in seen_ids
            ):
                continue

            seen_ids.add(
                yccd_record.yccd_id
            )

            selected.append(
                yccd_record
            )

        if not selected:
            raise ValueError(
                "Không chọn được YCCĐ "
                "cho tiết."
            )

        result = LessonObjectiveSelection(
            lesson_key=lesson_key,
            mode="PERIOD",
            period_in_lesson=(
                int(period_in_lesson)
            ),
            yccd_records=selected,
        )

        result.validate()

        return result

    @staticmethod
    def _select_lesson_objectives(
        records: list[YCCDRecord],
    ) -> list[YCCDRecord]:
        """
        Ở chế độ LESSON:
        ưu tiên các YCCĐ TRIEN_KHAI.

        Y00 CHINH_THUC dùng làm nguồn chuẩn/truy vết,
        không đưa trực tiếp thành danh sách mục tiêu
        triển khai của giáo án nếu đã có TRIEN_KHAI.
        """

        deployed = [
            record
            for record in records
            if (
                str(
                    record.yccd_type
                )
                .strip()
                .upper()
                == "TRIEN_KHAI"
            )
        ]

        if deployed:
             return deployed

        # Fallback:
        # nếu chưa có YCCĐ triển khai,
        # trả về YCCĐ hiện có thay vì
        # làm resolver thất bại ngay.
        return records