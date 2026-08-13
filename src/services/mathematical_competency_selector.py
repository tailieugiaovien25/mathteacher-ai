from models.lesson_objective_selection import (
    LessonObjectiveSelection,
)


class MathematicalCompetencySelector:
    """
    Chọn năng lực toán học từ YCCĐ bằng rule-based logic.

    Phiên bản v1.1:
    - Không dùng AI.
    - Chỉ trả về mã năng lực chuẩn.
    - Tránh nhận nhầm từ "tính" trong cụm "phép tính".
    """

    def select(
        self,
        selection: LessonObjectiveSelection,
    ) -> list[str]:

        selection.validate()

        if not selection.yccd_records:
            raise ValueError(
                "Không có YCCĐ để chọn năng lực."
            )

        selected: list[str] = []

        def add(code: str) -> None:
            if code not in selected:
                selected.append(code)

        for yccd in selection.yccd_records:
            text = (
                str(yccd.requirement)
                .strip()
                .lower()
            )

            # -------------------------------------------------
            # 1. TƯ DUY VÀ LẬP LUẬN TOÁN HỌC
            # -------------------------------------------------

            if any(
                keyword in text
                for keyword in [
                    "mô tả",
                    "giải thích",
                    "lập luận",
                    "nhận xét",
                    "so sánh",
                    "chứng minh",
                ]
            ):
                add("NLT_TDLL")

            # -------------------------------------------------
            # 2. GIẢI QUYẾT VẤN ĐỀ TOÁN HỌC
            #
            # Không dùng riêng từ "tính",
            # vì "phép tính" sẽ gây false positive.
            # -------------------------------------------------

            if any(
                keyword in text
                for keyword in [
                    "thực hiện",
                    "tính được",
                    "tính toán",
                    "vận dụng",
                    "giải quyết",
                    "tìm được",
                    "xác định được",
                ]
            ):
                add("NLT_GQVD")

            # -------------------------------------------------
            # 3. GIAO TIẾP TOÁN HỌC
            # -------------------------------------------------

            if any(
                keyword in text
                for keyword in [
                    "trình bày",
                    "trao đổi",
                    "diễn đạt",
                    "biểu diễn",
                    "thảo luận",
                ]
            ):
                add("NLT_GT")

            # -------------------------------------------------
            # 4. MÔ HÌNH HÓA TOÁN HỌC
            # -------------------------------------------------

            if any(
                keyword in text
                for keyword in [
                    "thực tiễn",
                    "thực tế",
                    "mô hình",
                    "tình huống thực tiễn",
                ]
            ):
                add("NLT_MHH")

            # -------------------------------------------------
            # 5. SỬ DỤNG CÔNG CỤ, PHƯƠNG TIỆN
            # -------------------------------------------------

            if any(
                keyword in text
                for keyword in [
                    "máy tính",
                    "phần mềm",
                    "công cụ",
                    "thước",
                    "compa",
                ]
            ):
                add("NLT_CCPT")

        return selected