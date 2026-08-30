# V57-B PHASE 1
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_CONTEXT_WIDGETS = {
    "selectbox", "multiselect", "radio", "checkbox", "toggle",
    "date_input", "number_input", "text_input",
}
_CONTEXT_HINTS = {
    "academic_year", "week", "subject", "component", "grade", "class",
    "timetable", "curriculum", "ppct", "lesson", "assignment",
}


@dataclass(frozen=True, slots=True)
class GuardFinding:
    file: str
    line: int
    code: str
    detail: str


def inspect_migrated_streamlit_file(path: Path) -> tuple[GuardFinding, ...]:
    """Strict only for pages explicitly migrated to Context Registry."""
    text = path.read_text(encoding="utf-8-sig")
    if "CONTEXT_REGISTRY_MIGRATED = True" not in text:
        return ()

    tree = ast.parse(text)
    findings: list[GuardFinding] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "st"
            and func.attr in _CONTEXT_WIDGETS
        ):
            continue

        label = ""
        if node.args and isinstance(node.args[0], ast.Constant):
            if isinstance(node.args[0].value, str):
                label = node.args[0].value

        key_text = ""
        has_key = False
        for kw in node.keywords:
            if kw.arg == "key":
                has_key = True
                try:
                    key_text = ast.unparse(kw.value)
                except Exception:
                    key_text = ""

        searchable = f"{label} {key_text}".lower()
        if not any(token in searchable for token in _CONTEXT_HINTS):
            continue

        if not has_key:
            findings.append(
                GuardFinding(
                    file=str(path),
                    line=node.lineno,
                    code="CONTEXT_WIDGET_MISSING_EXPLICIT_KEY",
                    detail=f"{func.attr}:{label}",
                )
            )

    return tuple(findings)


def inspect_many(paths: Iterable[Path]) -> tuple[GuardFinding, ...]:
    findings: list[GuardFinding] = []
    for path in paths:
        findings.extend(inspect_migrated_streamlit_file(path))
    return tuple(findings)
