from portal_v2.runtime.teacher_subject_assignment_consistency_runtime import (
    TeacherSubjectAssignmentConsistencyRuntime,
)


class FakeResponse:
    def __init__(
        self,
        data,
    ):
        self.data = data


class FakeQuery:
    def __init__(
        self,
        *,
        rows,
    ):
        self._rows = list(rows)
        self._filters = {}

    def select(
        self,
        *args,
        **kwargs,
    ):
        return self

    def eq(
        self,
        field,
        value,
    ):
        self._filters[field] = value
        return self

    def order(
        self,
        *args,
        **kwargs,
    ):
        return self

    def limit(
        self,
        *args,
        **kwargs,
    ):
        return self

    def execute(
        self,
    ):
        result = []

        for row in self._rows:
            if all(
                row.get(field) == value
                for field, value
                in self._filters.items()
            ):
                result.append(
                    dict(row)
                )

        return FakeResponse(
            result
        )


class FakeClient:
    def __init__(
        self,
        *,
        tables,
    ):
        self._tables = tables

    def table(
        self,
        name,
    ):
        return FakeQuery(
            rows=self._tables.get(
                name,
                (),
            )
        )


def test_runtime_reports_consistent_system_data():
    client = FakeClient(
        tables={
            "teacher_subject_registrations": (
                {
                    "registration_id": "reg-1",
                    "owner_id": "teacher-1",
                    "academic_year": "2026-2027",
                    "subject_id": "SUBJECT-A",
                    "component_id": "COMPONENT-A",
                    "status": "ACTIVE",
                },
            ),
            "teaching_assignments": (
                {
                    "assignment_id": "assignment-1",
                    "owner_id": "teacher-1",
                    "academic_year": "2026-2027",
                    "class_id": "CLASS-A",
                    "role": "TEACHING",
                    "subject_ref": "SUBJECT-A",
                    "component_ref": "COMPONENT-A",
                    "effective_from": "2026-09-01",
                    "effective_to": "2027-05-31",
                    "status": "ACTIVE",
                },
            ),
        }
    )

    result = (
        TeacherSubjectAssignmentConsistencyRuntime(
            client=client,
            user_id="teacher-1",
        )
        .audit(
            academic_year="2026-2027",
        )
    )

    assert result.is_consistent
    assert result.issues == ()


def test_runtime_reports_missing_registration():
    client = FakeClient(
        tables={
            "teacher_subject_registrations": (),
            "teaching_assignments": (
                {
                    "assignment_id": "assignment-1",
                    "owner_id": "teacher-1",
                    "academic_year": "2026-2027",
                    "class_id": "CLASS-A",
                    "role": "TEACHING",
                    "subject_ref": "SUBJECT-A",
                    "component_ref": "COMPONENT-A",
                    "effective_from": "2026-09-01",
                    "effective_to": "2027-05-31",
                    "status": "ACTIVE",
                },
            ),
        }
    )

    result = (
        TeacherSubjectAssignmentConsistencyRuntime(
            client=client,
            user_id="teacher-1",
        )
        .audit(
            academic_year="2026-2027",
        )
    )

    assert not result.is_consistent
    assert len(
        result.issues
    ) == 1


def test_runtime_requires_non_empty_user_id():
    try:
        TeacherSubjectAssignmentConsistencyRuntime(
            client=FakeClient(
                tables={}
            ),
            user_id=" ",
        )
    except ValueError as error:
        assert (
            "user_id must not be empty"
            in str(error)
        )
    else:
        raise AssertionError(
            "expected ValueError"
        )


def test_runtime_requires_non_empty_academic_year():
    runtime = (
        TeacherSubjectAssignmentConsistencyRuntime(
            client=FakeClient(
                tables={}
            ),
            user_id="teacher-1",
        )
    )

    try:
        runtime.audit(
            academic_year=" ",
        )
    except ValueError as error:
        assert (
            "academic_year must not be empty"
            in str(error)
        )
    else:
        raise AssertionError(
            "expected ValueError"
        )
