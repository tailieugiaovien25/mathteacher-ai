from assessment_generation_v2.adapters.supabase_assessment_curriculum_catalog import (
    SupabaseAssessmentCurriculumCatalog,
)


class Response:
    def __init__(self, data):
        self.data = data


class Query:
    def __init__(self, client):
        self.client = client
        self.operations = []

    def select(self, value):
        self.operations.append(
            ("select", value)
        )
        return self

    def eq(self, field, value):
        self.operations.append(
            ("eq", field, value)
        )
        return self

    def lte(self, field, value):
        self.operations.append(
            ("lte", field, value)
        )
        return self

    def gte(self, field, value):
        self.operations.append(
            ("gte", field, value)
        )
        return self

    def like(self, field, value):
        self.operations.append(
            ("like", field, value)
        )
        return self

    def in_(self, field, value):
        self.operations.append(
            ("in", field, tuple(value))
        )
        return self

    def order(self, field):
        self.operations.append(
            ("order", field)
        )
        return self

    def execute(self):
        self.client.last_operations = tuple(
            self.operations
        )

        return Response(
            self.client.response_data
        )


class Client:
    def __init__(self, response_data):
        self.response_data = response_data
        self.table_name = None
        self.last_operations = ()

    def table(self, name):
        self.table_name = name
        return Query(self)


def test_program_query_uses_canonical_program_table():
    client = Client(
        [
            {
                "program_code": "MOET-GDPT2018-MATH-THCS",
                "program_name": "Math",
                "subject_code": "MATH",
                "education_level": "THCS",
                "grade_min": 6,
                "grade_max": 9,
                "version_label": "GDPT-2018-CURRENT",
                "status": "ACTIVE",
            }
        ]
    )

    catalog = SupabaseAssessmentCurriculumCatalog(
        client=client
    )

    value = catalog.find_active_program(
        subject_code="MATH",
        grade_level=6,
    )

    assert client.table_name == (
        "assessment_curriculum_programs"
    )

    assert value is not None

    assert (
        "eq",
        "status",
        "ACTIVE",
    ) in client.last_operations


def test_topic_query_enforces_canonical_topic_prefix():
    client = Client(
        [
            {
                "topic_code": "CURR-NODE-MATH-G6-001",
                "program_code": "MOET-GDPT2018-MATH-THCS",
                "parent_topic_code": None,
                "grade_level": 6,
                "domain_code": "CONTENT_STRAND",
                "topic_name": "Số và Đại số",
                "sequence_number": 1,
                "status": "ACTIVE",
                "metadata": {
                    "canonical_node_type": (
                        "CONTENT_STRAND"
                    )
                },
            }
        ]
    )

    catalog = SupabaseAssessmentCurriculumCatalog(
        client=client
    )

    rows = catalog.list_topics(
        program_code="MOET-GDPT2018-MATH-THCS",
        grade_level=6,
    )

    assert client.table_name == (
        "assessment_curriculum_topics"
    )

    assert len(rows) == 1

    assert (
        "like",
        "topic_code",
        "CURR-NODE-%",
    ) in client.last_operations


def test_requirement_query_enforces_verified_status():
    client = Client(
        [
            {
                "requirement_code": "YCCD-MATH-06-0001",
                "program_code": "MOET-GDPT2018-MATH-THCS",
                "topic_code": "CURR-NODE-MATH-G6-001",
                "grade_level": 6,
                "requirement_text": "Yêu cầu cần đạt",
                "source_locator": "Lớp 6",
                "version_number": 1,
                "status": "ACTIVE",
                "metadata": {
                    "canonical_status": "VERIFIED"
                },
            }
        ]
    )

    catalog = SupabaseAssessmentCurriculumCatalog(
        client=client
    )

    rows = catalog.list_requirements(
        program_code="MOET-GDPT2018-MATH-THCS",
        grade_level=6,
        topic_codes=(
            "CURR-NODE-MATH-G6-001",
        ),
    )

    assert client.table_name == (
        "assessment_learning_requirements"
    )

    assert len(rows) == 1

    assert (
        "eq",
        "metadata->>canonical_status",
        "VERIFIED",
    ) in client.last_operations

    assert (
        "in",
        "topic_code",
        ("CURR-NODE-MATH-G6-001",),
    ) in client.last_operations


def test_empty_topic_filter_does_not_execute():
    client = Client([])

    catalog = SupabaseAssessmentCurriculumCatalog(
        client=client
    )

    rows = catalog.list_requirements(
        program_code="MOET-GDPT2018-MATH-THCS",
        grade_level=6,
        topic_codes=(),
    )

    assert rows == ()
