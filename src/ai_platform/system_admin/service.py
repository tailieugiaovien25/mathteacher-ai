from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_platform.config import AIPlatformConfig
from ai_platform.contracts import AIProvider, AIRequest


@dataclass(frozen=True)
class SystemAdminDiagnostic:
    checks: tuple[dict[str, Any], ...]


class SystemAdminAIService:
    """Read-only operational assistant. Mutations require explicit human action."""

    def __init__(self, provider: AIProvider | None = None, config: AIPlatformConfig | None = None):
        self.provider = provider
        self.config = config or AIPlatformConfig.from_environment()

    def diagnose(self, checks: tuple[dict[str, Any], ...]) -> SystemAdminDiagnostic:
        return SystemAdminDiagnostic(checks=tuple(checks))

    def explain(self, diagnostic: SystemAdminDiagnostic) -> str:
        if self.provider is None:
            return "AI local chưa được kết nối; báo cáo kiểm tra deterministic vẫn dùng được."
        prompt = (
            "Phân tích báo cáo vận hành MathTeacher AI dưới góc nhìn quản trị hệ thống. "
            "Chỉ nêu bằng chứng, nguyên nhân có thể xảy ra và bước kiểm tra an toàn. "
            "Không tự đề xuất thao tác xóa/sửa dữ liệu sản xuất.\n\n"
            f"REPORT:\n{diagnostic.checks}"
        )
        return self.provider.generate(AIRequest(
            task="system_diagnostics",
            prompt=prompt,
            system_prompt="Bạn là AI Quản trị hệ thống, ưu tiên an toàn, quan sát và khả năng khôi phục.",
        )).text
