from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _required(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    text=value.strip()
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    return text

@dataclass(frozen=True)
class CompetencyFramework:
    framework_id: str
    canonical_code: str
    framework_name: str
    framework_type: str
    subject_id: str | None = None
    version_label: str = "1.0"
    provenance_status: str = "REVIEWED"
    status: str = "ACTIVE"
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        for f in ("framework_id","canonical_code","framework_name","framework_type","version_label","provenance_status","status"):
            object.__setattr__(self,f,_required(getattr(self,f),f))

@dataclass(frozen=True)
class CompetencyIndicator:
    indicator_id: str
    framework_id: str
    canonical_code: str
    indicator_name: str
    indicator_text: str
    component_id: str | None = None
    source_code: str | None = None
    observable_flag: bool = True
    assessable_flag: bool = True
    version_label: str = "1.0"
    provenance_status: str = "REVIEWED"
    status: str = "ACTIVE"
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        for f in ("indicator_id","framework_id","canonical_code","indicator_name","indicator_text","version_label","provenance_status","status"):
            object.__setattr__(self,f,_required(getattr(self,f),f))

@dataclass(frozen=True)
class CompetencyGradeDescriptor:
    descriptor_id: str
    indicator_id: str
    grade_id: str
    canonical_code: str
    descriptor_text: str
    version_label: str = "1.0"
    provenance_status: str = "UNVERIFIED"
    status: str = "DRAFT"
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        for f in ("descriptor_id","indicator_id","grade_id","canonical_code","descriptor_text","version_label","provenance_status","status"):
            object.__setattr__(self,f,_required(getattr(self,f),f))
