from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping


class PromptProductType(str, Enum):
    LESSON_PLAN = "LESSON_PLAN"
    ASSESSMENT_MATRIX = "ASSESSMENT_MATRIX"
    ASSESSMENT_SPECIFICATION = "ASSESSMENT_SPECIFICATION"
    ASSESSMENT_EXAM = "ASSESSMENT_EXAM"


class PromptLifecycle(str, Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class PromptVariable:
    name: str
    label: str
    required: bool = True
    default_value: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Prompt variable name must not be blank")
        if not self.label.strip():
            raise ValueError("Prompt variable label must not be blank")


@dataclass(frozen=True)
class PromptFolder:
    folder_id: str
    label: str
    product_type: PromptProductType
    subject_ref: str
    component_ref: str = ""
    grade_level: str = ""

    def __post_init__(self) -> None:
        if not self.folder_id.strip() or not self.label.strip():
            raise ValueError("Prompt folder identity must not be blank")
        if not self.subject_ref.strip():
            raise ValueError("Prompt folder subject_ref must not be blank")


@dataclass(frozen=True)
class PromptTemplate:
    prompt_id: str
    folder: PromptFolder
    name: str
    version: int
    lifecycle: PromptLifecycle
    content: str
    variables: tuple[PromptVariable, ...]
    source_path: Path | None = None

    def __post_init__(self) -> None:
        if not self.prompt_id.strip() or not self.name.strip():
            raise ValueError("Prompt identity must not be blank")
        if self.version < 1:
            raise ValueError("Prompt version must be positive")
        if not self.content.strip():
            raise ValueError("Prompt content must not be blank")
        names = tuple(item.name for item in self.variables)
        if len(names) != len(set(names)):
            raise ValueError("Prompt variable names must be unique")


@dataclass(frozen=True)
class RenderedPrompt:
    prompt_id: str
    version: int
    product_type: PromptProductType
    subject_ref: str
    component_ref: str
    content: str
    inputs: Mapping[str, str]
