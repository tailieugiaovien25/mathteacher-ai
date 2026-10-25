from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModelCapability(str, Enum):
    GENERAL = "general"
    VIETNAMESE = "vietnamese"
    MATHEMATICS = "mathematics"
    REASONING = "reasoning"
    CODING = "coding"
    DOCUMENT = "document"
    MULTIMODAL = "multimodal"
    AGENTIC = "agentic"


@dataclass(frozen=True)
class ModelProfile:
    profile_id: str
    provider: str
    model: str
    capabilities: frozenset[ModelCapability]
    local_first: bool = True
    commercially_permissive: bool = True
    admin_enabled: bool = True
    notes: str = ""


def default_model_profiles() -> tuple[ModelProfile, ...]:
    """Known local profiles. IDs may be replaced by ADMIN without code changes."""
    return (
        ModelProfile(
            profile_id="qwen3-local-0.6b",
            provider="ollama",
            model="qwen3:0.6b",
            capabilities=frozenset({ModelCapability.GENERAL, ModelCapability.VIETNAMESE}),
            notes="Profile nhẹ cho máy RAM thấp; phù hợp kiểm thử/AI Trợ giảng Lite trên PC cá nhân.",
        ),
        ModelProfile(
            profile_id="qwen3-local-8b",
            provider="ollama",
            model="qwen3:8b",
            capabilities=frozenset({ModelCapability.GENERAL, ModelCapability.VIETNAMESE, ModelCapability.MATHEMATICS, ModelCapability.CODING, ModelCapability.AGENTIC}),
            notes="Mặc định nhẹ cho máy cá nhân; Ollama hiện cung cấp tag qwen3:8b.",
        ),
        ModelProfile(
            profile_id="qwen3-local-30b",
            provider="ollama",
            model="qwen3:30b",
            capabilities=frozenset({ModelCapability.GENERAL, ModelCapability.VIETNAMESE, ModelCapability.MATHEMATICS, ModelCapability.REASONING, ModelCapability.CODING, ModelCapability.AGENTIC}),
            notes="Tác vụ suy luận/agent nặng hơn; phù hợp máy có GPU/RAM tốt hơn.",
        ),
        ModelProfile(
            profile_id="deepseek-r1-reasoning",
            provider="ollama",
            model="deepseek-r1:32b",
            capabilities=frozenset({ModelCapability.REASONING, ModelCapability.MATHEMATICS, ModelCapability.CODING}),
            notes="Chuyên suy luận; dùng theo định tuyến nhiệm vụ, không mặc định cho mọi yêu cầu.",
        ),
       ModelProfile(
            profile_id="gemma4-cloud",
            provider="ollama",
            model="gemma4:cloud",
            capabilities=frozenset({
                ModelCapability.GENERAL,
                ModelCapability.VIETNAMESE,
                ModelCapability.MATHEMATICS,
                ModelCapability.REASONING,
            }),
            local_first=False,
            notes="Ollama Cloud; dùng khi máy local không đủ tài nguyên cho Trợ giảng.",
        ),
        ModelProfile(
            profile_id="mistral-document-multimodal",
            provider="ollama",
            model="mistral-small3.1:24b",
            capabilities=frozenset({ModelCapability.GENERAL, ModelCapability.DOCUMENT, ModelCapability.MULTIMODAL, ModelCapability.VIETNAMESE}),
            notes="Nhánh tài liệu/ảnh; Ollama cung cấp tag 24B với vision và context dài.",
        ),
    )
