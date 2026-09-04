from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


def merge_with_parent_authority(
    *, parent: Mapping[str, Any] | None, child: Mapping[str, Any] | None
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Merge a child payload under an authoritative parent.

    Parent leaf values always win. Child values are accepted only at paths the
    parent has not defined. Returned paths identify attempted conflicts.
    """
    conflicts: list[str] = []

    def merge(parent_value: Any, child_value: Any, path: tuple[str, ...]) -> Any:
        if isinstance(parent_value, Mapping) and isinstance(child_value, Mapping):
            result = deepcopy(dict(child_value))
            for key, value in parent_value.items():
                if key in child_value:
                    result[key] = merge(value, child_value[key], path + (str(key),))
                else:
                    result[key] = deepcopy(value)
            return result
        if parent_value != child_value:
            conflicts.append(".".join(path))
        return deepcopy(parent_value)

    effective = merge(dict(parent or {}), dict(child or {}), ())
    return effective, tuple(sorted({path for path in conflicts if path}))


def remove_parent_locked_values(
    *, parent: Mapping[str, Any] | None, child: Mapping[str, Any] | None
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Remove child fields already governed by parent before persistence."""
    removed: list[str] = []

    def clean(parent_value: Any, child_value: Any, path: tuple[str, ...]) -> Any:
        if not isinstance(child_value, Mapping):
            return deepcopy(child_value)
        result = {}
        parent_map = parent_value if isinstance(parent_value, Mapping) else {}
        for key, value in child_value.items():
            next_path = path + (str(key),)
            if key not in parent_map:
                result[key] = deepcopy(value)
                continue
            if isinstance(value, Mapping) and isinstance(parent_map[key], Mapping):
                nested = clean(parent_map[key], value, next_path)
                if nested:
                    result[key] = nested
            else:
                removed.append(".".join(next_path))
        return result

    return clean(dict(parent or {}), dict(child or {}), ()), tuple(sorted(set(removed)))
