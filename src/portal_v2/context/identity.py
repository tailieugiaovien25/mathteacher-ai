from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ContextIdentity:
    user_id: str
    context_id: str

    def __post_init__(self) -> None:
        if not str(self.user_id).strip():
            raise ValueError("user_id is required")
        if not str(self.context_id).strip():
            raise ValueError("context_id is required")

    @classmethod
    def create(cls, *, user_id: str) -> "ContextIdentity":
        return cls(
            user_id=str(user_id),
            context_id=str(uuid4()),
        )
