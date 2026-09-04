from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Mapping

from .models import (
    PromptLifecycle,
    PromptTemplate,
    RenderedPrompt,
)


_TOKEN = re.compile(r"\{\{([a-zA-Z][a-zA-Z0-9_]*)\}\}")


class PromptRenderError(ValueError):
    pass


class PromptLibraryService:
    def __init__(self, prompts: Iterable[PromptTemplate]) -> None:
        self._prompts = tuple(prompts)
        identities = tuple((item.prompt_id, item.version) for item in self._prompts)
        if len(identities) != len(set(identities)):
            raise ValueError("Prompt id and version pairs must be unique")

    @property
    def prompts(self) -> tuple[PromptTemplate, ...]:
        return self._prompts

    def active_prompts(self) -> tuple[PromptTemplate, ...]:
        return tuple(
            item for item in self._prompts
            if item.lifecycle is PromptLifecycle.ACTIVE
        )

    def find_active(
        self,
        *,
        subject_ref: str,
        product_type,
        component_ref: str = "",
        grade_level: str = "",
    ) -> tuple[PromptTemplate, ...]:
        return tuple(
            item for item in self.active_prompts()
            if item.folder.subject_ref == subject_ref
            and item.folder.product_type == product_type
            and (not component_ref or item.folder.component_ref == component_ref)
            and (not grade_level or item.folder.grade_level in ("", grade_level))
        )

    def render(
        self,
        prompt: PromptTemplate,
        values: Mapping[str, object],
    ) -> RenderedPrompt:
        if prompt.lifecycle is not PromptLifecycle.ACTIVE:
            raise PromptRenderError("Only ACTIVE prompts can be used by USER")

        normalized = {
            str(name): str(value if value is not None else "").strip()
            for name, value in values.items()
        }
        missing = tuple(
            variable.label
            for variable in prompt.variables
            if variable.required
            and not normalized.get(variable.name, variable.default_value).strip()
        )
        if missing:
            raise PromptRenderError(
                "Missing required prompt inputs: " + ", ".join(missing)
            )

        resolved = {
            variable.name: normalized.get(
                variable.name,
                variable.default_value,
            ) or variable.default_value
            for variable in prompt.variables
        }
        content = _TOKEN.sub(lambda match: resolved.get(match.group(1), match.group(0)), prompt.content)
        unresolved = tuple(sorted(set(_TOKEN.findall(content))))
        if unresolved:
            raise PromptRenderError(
                "Unresolved prompt variables: " + ", ".join(unresolved)
            )
        return RenderedPrompt(
            prompt_id=prompt.prompt_id,
            version=prompt.version,
            product_type=prompt.folder.product_type,
            subject_ref=prompt.folder.subject_ref,
            component_ref=prompt.folder.component_ref,
            content=content,
            inputs=resolved,
        )

    @staticmethod
    def transition(
        prompt: PromptTemplate,
        lifecycle: PromptLifecycle,
    ) -> PromptTemplate:
        allowed = {
            PromptLifecycle.DRAFT: {PromptLifecycle.REVIEW},
            PromptLifecycle.REVIEW: {
                PromptLifecycle.DRAFT,
                PromptLifecycle.ACTIVE,
            },
            PromptLifecycle.ACTIVE: {PromptLifecycle.RETIRED},
            PromptLifecycle.RETIRED: set(),
        }
        if lifecycle not in allowed[prompt.lifecycle]:
            raise ValueError(
                f"Invalid prompt lifecycle transition: {prompt.lifecycle} -> {lifecycle}"
            )
        return replace(prompt, lifecycle=lifecycle)


def read_prompt_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").strip()
