from __future__ import annotations

from ai_platform.config import AIPlatformConfig
from ai_platform.contracts import AIProvider, AIRequest


class MarketingAIService:
    """Commercial-phase assistant. It cannot send campaigns or commit commercial actions."""

    def __init__(self, provider: AIProvider | None = None, config: AIPlatformConfig | None = None):
        self.provider = provider
        self.config = config or AIPlatformConfig.from_environment()

    def enabled(self) -> bool:
        return self.config.marketing_runtime_enabled

    def draft(self, *, objective: str, audience: str, channel: str) -> str:
        if not self.enabled():
            raise RuntimeError("AI Marketing đang tắt; chỉ kích hoạt khi hệ thống chuyển sang chế độ thương mại.")
        if self.provider is None:
            raise RuntimeError("Chưa có AI provider local.")
        prompt = (
            "Tạo bản nháp marketing cho MathTeacher AI. Không tự gửi, không cam kết giá, "
            "không đưa tuyên bố chưa được xác minh.\n"
            f"Mục tiêu: {objective}\nĐối tượng: {audience}\nKênh: {channel}"
        )
        return self.provider.generate(AIRequest(
            task="marketing_draft",
            prompt=prompt,
            system_prompt="Bạn là AI Marketing hỗ trợ thương mại, mọi nội dung phải chờ con người duyệt trước khi phát hành.",
        )).text
