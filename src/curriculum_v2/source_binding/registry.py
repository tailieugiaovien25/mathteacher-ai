"""Exact source-to-canonical binding registry.

The registry is intentionally deterministic and fail-closed:
- exact source identity only,
- VERIFIED bindings only at runtime,
- zero verified matches fail,
- multiple verified matches fail,
- no title/sequence/fuzzy fallback,
- batch resolution deduplicates canonical lesson IDs while preserving source
  order so multi-period source items can point to one canonical lesson.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Protocol

from .models import (
    CurriculumSourceItem,
    SourceCanonicalBinding,
    SourceItemIdentity,
)


class SourceCanonicalBindingResolutionError(
    RuntimeError
):
    """Raised when exact verified binding resolution is unsafe."""


class SourceCanonicalBindingRegistry(Protocol):
    def resolve_verified(
        self,
        item: CurriculumSourceItem,
    ) -> SourceCanonicalBinding:
        """Resolve exactly one VERIFIED binding."""

    def resolve_many_verified(
        self,
        items: Sequence[CurriculumSourceItem],
    ) -> tuple[SourceCanonicalBinding, ...]:
        """Resolve many items with stable canonical dedupe."""


class InMemorySourceCanonicalBindingRegistry:
    """Pure in-memory implementation for tests and file-backed data."""

    def __init__(
        self,
        bindings: Iterable[
            SourceCanonicalBinding
        ],
    ) -> None:
        normalized = tuple(bindings)

        if any(
            not isinstance(
                item,
                SourceCanonicalBinding,
            )
            for item in normalized
        ):
            raise TypeError(
                "bindings must contain "
                "SourceCanonicalBinding values"
            )

        binding_ids = tuple(
            item.binding_id
            for item in normalized
        )

        if len(set(binding_ids)) != len(
            binding_ids
        ):
            raise ValueError(
                "duplicate binding_id is not allowed"
            )

        by_identity: dict[
            SourceItemIdentity,
            list[SourceCanonicalBinding],
        ] = defaultdict(list)

        for binding in normalized:
            by_identity[
                binding.identity
            ].append(binding)

        self._bindings = normalized
        self._by_identity = {
            key: tuple(value)
            for key, value in by_identity.items()
        }

    def resolve_verified(
        self,
        item: CurriculumSourceItem,
    ) -> SourceCanonicalBinding:
        if not isinstance(
            item,
            CurriculumSourceItem,
        ):
            raise TypeError(
                "item must be CurriculumSourceItem"
            )

        matches = tuple(
            binding
            for binding in self._by_identity.get(
                item.identity,
                (),
            )
            if binding.status == "VERIFIED"
        )

        if not matches:
            raise SourceCanonicalBindingResolutionError(
                "no VERIFIED source-to-canonical binding "
                "matches the exact source identity"
            )

        if len(matches) != 1:
            raise SourceCanonicalBindingResolutionError(
                "VERIFIED source-to-canonical binding is "
                "ambiguous for the exact source identity"
            )

        return matches[0]

    def resolve_many_verified(
        self,
        items: Sequence[CurriculumSourceItem],
    ) -> tuple[SourceCanonicalBinding, ...]:
        if isinstance(
            items,
            (str, bytes),
        ):
            raise TypeError(
                "items must be a sequence of "
                "CurriculumSourceItem values"
            )

        resolved: list[
            SourceCanonicalBinding
        ] = []
        seen_lesson_ids: set[str] = set()

        for item in items:
            binding = self.resolve_verified(
                item
            )

            if (
                binding.canonical_lesson_id
                in seen_lesson_ids
            ):
                continue

            seen_lesson_ids.add(
                binding.canonical_lesson_id
            )
            resolved.append(binding)

        return tuple(resolved)
