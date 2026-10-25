from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class AIOwnership(str, Enum):
    ADMIN = "admin"
    USER = "user"
    SYSTEM = "system"


class AIActionClass(str, Enum):
    READ_ONLY = "read_only"
    ADVISORY = "advisory"
    MUTATING = "mutating"
    GOVERNANCE = "governance"


@dataclass(frozen=True)
class AIKernelRequest:
    task_id: str
    prompt: str
    owner: AIOwnership = AIOwnership.USER
    action: AIActionClass = AIActionClass.ADVISORY
    requested_capabilities: tuple[str, ...] = ()
    skill_id: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id is required")
        if not self.prompt.strip():
            raise ValueError("prompt is required")


@dataclass(frozen=True)
class AIKernelResponse:
    text: str
    provider: str
    model: str
    profile_id: str
    task_id: str
    audit_id: str
    action: AIActionClass
    used_fallback: bool = False
