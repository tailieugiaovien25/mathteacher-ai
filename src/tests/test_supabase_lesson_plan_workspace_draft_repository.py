from __future__ import annotations

from dataclasses import replace

from lesson_planning_v2.adapters.supabase_lesson_plan_workspace_draft_repository import (
    SupabaseLessonPlanWorkspaceDraftRepository,
)
from lesson_planning_v2.workspace_draft import (
    LessonPlanWorkspaceDraft,
)


class _Response:
    def __init__(
        self,
        data,
    ):
        self.data = data


class _Query:
    def __init__(
        self,
        table,
    ):
        self.table = table
        self.filters = []
        self.payload = None
        self.on_conflict = None

    def upsert(
        self,
        payload,
        *,
        on_conflict=None,
    ):
        self.payload = dict(
            payload
        )
        self.on_conflict = (
            on_conflict
        )
        self.table.last_upsert = self
        return self

    def select(
        self,
        _columns,
    ):
        return self

    def eq(
        self,
        field,
        value,
    ):
        self.filters.append(
            (
                field,
                value,
            )
        )
        return self

    def limit(
        self,
        _value,
    ):
        return self

    def execute(
        self,
    ):
        if self.payload is not None:
            key = (
                self.payload[
                    "teacher_user_id"
                ],
                self.payload[
                    "draft_id"
                ],
            )

            self.table.rows[
                key
            ] = dict(
                self.payload
            )

            return _Response(
                [
                    dict(
                        self.payload
                    )
                ]
            )

        rows = []

        for row in self.table.rows.values():
            matches = all(
                row.get(field)
                == value
                for field, value
                in self.filters
            )

            if matches:
                rows.append(
                    dict(row)
                )

        return _Response(
            rows[:1]
        )


class _Table:
    def __init__(self):
        self.rows = {}
        self.last_upsert = None

    def query(self):
        return _Query(
            self
        )


class _Client:
    def __init__(self):
        self.tables = {}

    def table(
        self,
        name,
    ):
        table = self.tables.setdefault(
            name,
            _Table(),
        )

        return table.query()


def _draft(
    *,
    teacher_user_id="teacher-a",
):
    return LessonPlanWorkspaceDraft(
        draft_id="draft-001",
        teacher_user_id=(
            teacher_user_id
        ),
        academic_year="2026-2027",
        week_number=1,
        subject_ref="subject-math",
        selection_mode="LESSON",
        selection_unit_id="lesson-7",
        objectives_text="Mục tiêu",
        materials_text="Thiết bị",
        teaching_process_text=(
            "Tiến trình"
        ),
        class_or_grade_ref="6A2",
        lesson_id="lesson-7",
        title=(
            "Bài 7. Thứ tự thực hiện "
            "các phép tính"
        ),
        metadata={
            "source": "test",
        },
    )


def test_save_and_get_round_trip():
    client = _Client()

    repository = (
        SupabaseLessonPlanWorkspaceDraftRepository(
            client=client,
        )
    )

    original = _draft()

    saved = repository.save(
        original
    )

    loaded = repository.get(
        draft_id=original.draft_id,
        teacher_user_id=(
            original.teacher_user_id
        ),
    )

    assert saved == original
    assert loaded == original


def test_save_uses_teacher_and_draft_conflict_key():
    client = _Client()

    repository = (
        SupabaseLessonPlanWorkspaceDraftRepository(
            client=client,
        )
    )

    repository.save(
        _draft()
    )

    table = client.tables[
        repository.TABLE_NAME
    ]

    assert (
        table.last_upsert.on_conflict
        == "teacher_user_id,draft_id"
    )


def test_get_is_teacher_scoped():
    client = _Client()

    repository = (
        SupabaseLessonPlanWorkspaceDraftRepository(
            client=client,
        )
    )

    repository.save(
        _draft(
            teacher_user_id="teacher-a",
        )
    )

    assert repository.get(
        draft_id="draft-001",
        teacher_user_id="teacher-b",
    ) is None


def test_same_draft_id_can_exist_for_two_teachers():
    client = _Client()

    repository = (
        SupabaseLessonPlanWorkspaceDraftRepository(
            client=client,
        )
    )

    teacher_a = _draft(
        teacher_user_id="teacher-a",
    )

    teacher_b = replace(
        teacher_a,
        teacher_user_id="teacher-b",
        objectives_text=(
            "Mục tiêu của giáo viên B"
        ),
    )

    repository.save(
        teacher_a
    )

    repository.save(
        teacher_b
    )

    assert repository.get(
        draft_id="draft-001",
        teacher_user_id="teacher-a",
    ) == teacher_a

    assert repository.get(
        draft_id="draft-001",
        teacher_user_id="teacher-b",
    ) == teacher_b


def test_save_replaces_same_teacher_draft():
    client = _Client()

    repository = (
        SupabaseLessonPlanWorkspaceDraftRepository(
            client=client,
        )
    )

    original = _draft()

    changed = replace(
        original,
        objectives_text=(
            "Mục tiêu đã sửa"
        ),
    )

    repository.save(
        original
    )

    repository.save(
        changed
    )

    loaded = repository.get(
        draft_id=changed.draft_id,
        teacher_user_id=(
            changed.teacher_user_id
        ),
    )

    assert loaded == changed


def test_invalid_client_rejected():
    try:
        SupabaseLessonPlanWorkspaceDraftRepository(
            client=None,
        )
    except ValueError as error:
        assert (
            "client must not be None"
            in str(error)
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )
