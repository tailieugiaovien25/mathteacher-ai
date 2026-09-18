"""Generic source-to-canonical binding foundation."""

from .models import (
    CurriculumSourceItem,
    SourceCanonicalBinding,
    SourceCanonicalBindingProvenance,
    SourceCanonicalBindingValidationError,
    SourceItemIdentity,
)
from .registry import (
    InMemorySourceCanonicalBindingRegistry,
    SourceCanonicalBindingRegistry,
    SourceCanonicalBindingResolutionError,
)

__all__ = [
    "CurriculumSourceItem",
    "SourceCanonicalBinding",
    "SourceCanonicalBindingProvenance",
    "SourceCanonicalBindingRegistry",
    "SourceCanonicalBindingResolutionError",
    "SourceCanonicalBindingValidationError",
    "SourceItemIdentity",
    "InMemorySourceCanonicalBindingRegistry",
]
