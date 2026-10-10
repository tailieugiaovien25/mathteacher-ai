from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol


@dataclass(frozen=True)
class AIRequest:
    task: str
    prompt: str
    system_prompt: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task.strip() or not self.prompt.strip():
            raise ValueError("task and prompt are required")


@dataclass(frozen=True)
class AIResponse:
    text: str
    provider: str
    model: str
    used_fallback: bool = False


class AIProvider(Protocol):
    provider_id: str
    model: str

    def generate(self, request: AIRequest) -> AIResponse:
        ...
