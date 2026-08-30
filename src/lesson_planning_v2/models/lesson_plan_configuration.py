from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class LessonPlanConfigurationSnapshot:
    profile_id: str
    profile_code: str
    profile_name: str
    subject_ref: str
    component_ref: str
    configuration_version_id: str
    version_number: int
    configuration_payload: Mapping[str, Any]

    def payload_section(self, name: str) -> Mapping[str, Any]:
        value = self.configuration_payload.get(name, {})
        return value if isinstance(value, Mapping) else {}
