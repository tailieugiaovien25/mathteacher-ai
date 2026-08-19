from __future__ import annotations

from typing import Any

from educational_planning_v2.models.admin_teacher_directory import (
    AdminTeacherDirectoryEntry,
)
from educational_planning_v2.repositories.admin_teacher_directory_repository import (
    AdminTeacherDirectoryRepository,
)


class SupabaseAdminTeacherDirectoryRepository(
    AdminTeacherDirectoryRepository
):
    PROFILE_TABLE = "teacher_profiles"

    def __init__(
        self,
        *,
        client: Any,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        self._client = client

    def list_teachers(
        self,
    ) -> tuple[
        AdminTeacherDirectoryEntry,
        ...,
    ]:
        profile_response = (
            self._client
            .table(self.PROFILE_TABLE)
            .select(
                "user_id,teacher_code,"
                "full_name,school_name"
            )
            .execute()
        )

        profile_rows = self._response_rows(
            profile_response
        )

        entries = []

        for row in profile_rows:
            user_id = str(
                row.get(
                    "user_id",
                    "",
                )
                or ""
            ).strip()

            if not user_id:
                continue

            entries.append(
                AdminTeacherDirectoryEntry(
                    user_id=user_id,
                    teacher_code=str(
                        row.get(
                            "teacher_code",
                            "",
                        )
                        or ""
                    ),
                    full_name=str(
                        row.get(
                            "full_name",
                            "",
                        )
                        or ""
                    ),
                    school_name=str(
                        row.get(
                            "school_name",
                            "",
                        )
                        or ""
                    ),
                )
            )

        return tuple(
            sorted(
                entries,
                key=lambda item: (
                    item.full_name.casefold(),
                    item.teacher_code.casefold(),
                    item.user_id,
                ),
            )
        )

    @staticmethod
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        data = getattr(
            response,
            "data",
            None,
        )

        if data is None:
            return []

        if not isinstance(
            data,
            list,
        ):
            raise TypeError(
                "Supabase response data must be a list"
            )

        if not all(
            isinstance(
                row,
                dict,
            )
            for row in data
        ):
            raise TypeError(
                "Supabase response rows must be dict"
            )

        return data
