"""Supabase adapter for the authenticated teacher's profile."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from educational_planning_v2.models import TeacherProfile


class SupabaseTeacherProfileRepository:
    def __init__(self, client: Any, user_id: str, table_name: str = "teacher_profiles") -> None:
        self._client = client
        self._user_id = self._required_text(user_id, "user_id")
        self._table_name = self._required_text(table_name, "table_name")

    def save(self, profile: TeacherProfile) -> TeacherProfile:
        if not isinstance(profile, TeacherProfile):
            raise TypeError("profile must be a TeacherProfile")
        row = {
            "user_id": self._user_id,
            "teacher_code": profile.teacher_code,
            "full_name": profile.full_name,
            "school_name": profile.school_name,
            "subjects": list(profile.subjects),
            "grade_levels": list(profile.grade_levels),
            "default_academic_year": profile.default_academic_year,
            "show_teacher_name": profile.show_teacher_name,
            "show_school_name": profile.show_school_name,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        response = self._client.table(self._table_name).upsert(
            row, on_conflict="user_id"
        ).execute()
        rows = self._response_rows(response)
        return self._from_row(rows[0]) if rows else profile

    def get(self) -> TeacherProfile | None:
        response = (
            self._client.table(self._table_name)
            .select(
                "teacher_code,full_name,school_name,subjects,grade_levels,"
                "default_academic_year,show_teacher_name,show_school_name"
            )
            .eq("user_id", self._user_id)
            .limit(1)
            .execute()
        )
        rows = self._response_rows(response)
        return self._from_row(rows[0]) if rows else None

    @staticmethod
    def _from_row(row: dict[str, Any]) -> TeacherProfile:
        return TeacherProfile(
            teacher_code=row["teacher_code"],
            full_name=row["full_name"],
            school_name=row["school_name"],
            subjects=tuple(row["subjects"]),
            grade_levels=tuple(row["grade_levels"]),
            default_academic_year=row["default_academic_year"],
            show_teacher_name=row["show_teacher_name"],
            show_school_name=row["show_school_name"],
        )

    @staticmethod
    def _response_rows(response: Any) -> list[dict[str, Any]]:
        rows = getattr(response, "data", None)
        if rows is None:
            raise ValueError("Supabase response does not contain data")
        if not isinstance(rows, list):
            raise TypeError("Supabase response data must be a list")
        return rows

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be empty")
        return normalized
