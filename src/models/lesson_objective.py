from dataclasses import dataclass, field
from typing import Any


VALID_OBJECTIVE_TYPES = {
    "KIEN_THUC",
    "NANG_LUC",
    "PHAM_CHAT",
}

VALID_STATUSES = {
    "draft",
    "approved",
    "deprecated",
}


@dataclass
class LessonObjective:
    """Một mục tiêu trong phần I. MỤC TIÊU của giáo án."""

    objective_id: str
    lesson_key: str
    objective_type: str
    content: str
    source_yccd_ids: list[str] = field(
        default_factory=list
    )
    order: int = 1
    status: str = "draft"

    def validate(self) -> None:
        if not self._clean_text(
            self.objective_id
        ):
            raise ValueError(
                "OBJECTIVE_ID không được để trống."
            )

        if not self._clean_text(
            self.lesson_key
        ):
            raise ValueError(
                "LESSON_KEY không được để trống."
            )

        if not self._clean_text(
            self.content
        ):
            raise ValueError(
                "CONTENT không được để trống."
            )

        normalized_type = (
            self._clean_text(
                self.objective_type
            ).upper()
        )

        if (
            normalized_type
            not in VALID_OBJECTIVE_TYPES
        ):
            raise ValueError(
                "OBJECTIVE_TYPE không hợp lệ: "
                f"{self.objective_type}"
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
                "ORDER phải là số nguyên."
            ) from error

        if order_number <= 0:
            raise ValueError(
                "ORDER phải lớn hơn 0."
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
                "STATUS không hợp lệ: "
                f"{self.status}"
            )

        # Kiến thức bắt buộc phải truy vết về YCCĐ.
        if (
            normalized_type
            == "KIEN_THUC"
            and not self.source_yccd_ids
        ):
            raise ValueError(
                "Mục tiêu KIEN_THUC bắt buộc "
                "phải có SOURCE_YCCD_IDS."
            )

        # Không cho ID nguồn rỗng.
        for yccd_id in self.source_yccd_ids:
            if not self._clean_text(
                yccd_id
            ):
                raise ValueError(
                    "SOURCE_YCCD_IDS "
                    "không được chứa ID rỗng."
                )

        # Không cho trùng YCCD_ID nguồn.
        normalized_ids = [
            self._clean_text(
                yccd_id
            )
            for yccd_id
            in self.source_yccd_ids
        ]

        if (
            len(normalized_ids)
            != len(set(normalized_ids))
        ):
            raise ValueError(
                "SOURCE_YCCD_IDS "
                "không được trùng."
            )

    @property
    def normalized_type(self) -> str:
        return (
            self._clean_text(
                self.objective_type
            ).upper()
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        self.validate()

        return {
            "OBJECTIVE_ID": self.objective_id,
            "LESSON_KEY": self.lesson_key,
            "OBJECTIVE_TYPE": (
                self.normalized_type
            ),
            "CONTENT": self.content,
            "SOURCE_YCCD_IDS": list(
                self.source_yccd_ids
            ),
            "ORDER": int(
                self.order
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