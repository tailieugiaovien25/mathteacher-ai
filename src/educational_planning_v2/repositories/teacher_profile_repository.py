"""Storage-independent contract for a teacher-owned profile."""

from __future__ import annotations

from typing import Protocol

from educational_planning_v2.models import TeacherProfile


class TeacherProfileRepository(Protocol):
    def save(self, profile: TeacherProfile) -> TeacherProfile: ...

    def get(self) -> TeacherProfile | None: ...
