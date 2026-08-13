from models.lesson_objective import (
    LessonObjective,
)
from models.lesson_objective_selection import (
    LessonObjectiveSelection,
)


class ObjectiveBuilder:
    """
    Xây dựng mục tiêu giáo án từ YCCĐ đã được Resolver chọn.

    Phiên bản v1:
    - Chỉ tạo mục tiêu KIEN_THUC.
    - Mỗi YCCĐ tạo thành một mục tiêu kiến thức.
    - Mỗi mục tiêu truy vết trực tiếp về YCCD_ID nguồn.
    - Chưa sử dụng AI.
    """

    def build_knowledge_objectives(
        self,
        selection: LessonObjectiveSelection,
    ) -> list[LessonObjective]:

        # -----------------------------------------------------
        # 1. Kiểm tra selection đầu vào
        # -----------------------------------------------------

        selection.validate()

        if not selection.yccd_records:
            raise ValueError(
                "Không có YCCĐ để xây dựng mục tiêu."
            )

        # -----------------------------------------------------
        # 2. Tạo mục tiêu kiến thức
        # -----------------------------------------------------

        objectives: list[
            LessonObjective
        ] = []

        for index, yccd in enumerate(
            selection.yccd_records,
            start=1,
        ):
            objective = LessonObjective(
                objective_id=(
                    f"{selection.lesson_key}"
                    f"_OBJ_KT{index:02d}"
                ),
                lesson_key=(
                    selection.lesson_key
                ),
                objective_type="KIEN_THUC",
                content=(
                    str(
                        yccd.requirement
                    ).strip()
                ),
                source_yccd_ids=[
                    yccd.yccd_id
                ],
                order=index,
                status="draft",
            )

            objective.validate()

            objectives.append(
                objective
            )

        # -----------------------------------------------------
        # 3. Kiểm tra coverage
        # -----------------------------------------------------

        source_ids = {
            source_id
            for objective in objectives
            for source_id
            in objective.source_yccd_ids
        }

        expected_ids = {
            yccd.yccd_id
            for yccd
            in selection.yccd_records
        }

        if source_ids != expected_ids:
            raise ValueError(
                "Không bảo toàn đầy đủ "
                "truy vết YCCĐ -> mục tiêu."
            )

        return objectives