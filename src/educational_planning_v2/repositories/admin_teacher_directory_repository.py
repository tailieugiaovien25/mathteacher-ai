from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.admin_teacher_directory import (
    AdminTeacherDirectoryEntry,
)


class AdminTeacherDirectoryRepository(
    ABC
):
    @abstractmethod
    def list_teachers(
        self,
    ) -> tuple[
        AdminTeacherDirectoryEntry,
        ...,
    ]:
        raise NotImplementedError
