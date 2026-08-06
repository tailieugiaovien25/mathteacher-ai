from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BaseModel:
    """Lớp nền dùng chung cho các mô hình dữ liệu."""

    source_file: str = ""
    source_sheet: str = ""
    source_row: int | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_warning(self, message: str) -> None:
        """Thêm cảnh báo hợp lệ và không trùng lặp."""
        normalized_message = message.strip()

        if not normalized_message:
            return

        if normalized_message not in self.warnings:
            self.warnings.append(normalized_message)

    def has_warnings(self) -> bool:
        """Kiểm tra model có cảnh báo hay không."""
        return bool(self.warnings)

    def clear_warnings(self) -> None:
        """Xóa toàn bộ cảnh báo."""
        self.warnings.clear()

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Thêm hoặc cập nhật một giá trị metadata."""
        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "Metadata key không được để trống."
            )

        self.metadata[normalized_key] = value

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Đọc metadata an toàn."""
        return self.metadata.get(
            key,
            default,
        )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển model thành dictionary."""
        return asdict(self)