from portal_v2.runtime.assessment_builder_requirement_recommendation_presentation_runtime import (
    AssessmentBuilderRequirementRecommendationPresentationRuntime,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows):
        self.rows = [dict(row) for row in rows]
        self.field = None
        self.values = None

    def select(self, _columns):
        return self

    def in_(self, field, values):
        self.field = field
        self.values = set(values)
        return self

    def execute(self):
        rows = self.rows
        if self.field is not None:
            rows = [
                row for row in rows
                if row.get(self.field) in self.values
            ]
        return FakeResponse(rows)


class FakeClient:
    def __init__(self):
        self.tables = {
            "textbook_units": [
                {
                    "textbook_unit_id": "lesson-1",
                    "parent_unit_id": "chapter-1",
                    "unit_type": "LESSON",
                    "canonical_code": "L001",
                    "title": "Lesson 1",
                    "status": "ACTIVE",
                },
                {
                    "textbook_unit_id": "lesson-2",
                    "parent_unit_id": "chapter-1",
                    "unit_type": "LESSON",
                    "canonical_code": "L002",
                    "title": "Lesson 2",
                    "status": "ACTIVE",
                },
                {
                    "textbook_unit_id": "chapter-1",
                    "parent_unit_id": None,
                    "unit_type": "CHAPTER",
                    "canonical_code": "CH01",
                    "title": "Chapter 1",
                    "status": "ACTIVE",
                },
            ],
            "assessment_learning_requirements": [
                {
                    "requirement_code": "Y1",
                    "topic_code": "T1",
                    "grade_level": 7,
                    "requirement_text": "Requirement 1",
                    "status": "ACTIVE",
                },
                {
                    "requirement_code": "Y2",
                    "topic_code": "T2",
                    "grade_level": 7,
                    "requirement_text": "Requirement 2",
                    "status": "ACTIVE",
                },
                {
                    "requirement_code": "Y3",
                    "topic_code": "T1",
                    "grade_level": 7,
                    "requirement_text": "Requirement 3",
                    "status": "ACTIVE",
                },
            ],
            "assessment_curriculum_topics": [
                {
                    "topic_code": "T1",
                    "grade_level": 7,
                    "topic_name": "Topic 1",
                    "status": "ACTIVE",
                },
                {
                    "topic_code": "T2",
                    "grade_level": 7,
                    "topic_name": "Topic 2",
                    "status": "ACTIVE",
                },
            ],
        }

    def table(self, name):
        return FakeQuery(self.tables[name])


def test_presentation_runtime_preserves_exact_input_order_and_enriches_text():
    result = AssessmentBuilderRequirementRecommendationPresentationRuntime(
        client=FakeClient()
    ).load(
        textbook_unit_ids=("lesson-2", "lesson-1"),
        requirement_codes=("Y3", "Y1", "Y2"),
    )

    assert [row.textbook_unit_id for row in result.lessons] == [
        "lesson-2",
        "lesson-1",
    ]
    assert [row.title for row in result.lessons] == [
        "Lesson 2",
        "Lesson 1",
    ]
    assert [row.chapter_title for row in result.lessons] == [
        "Chapter 1",
        "Chapter 1",
    ]
    assert result.topic_codes == ("T1", "T2")
    assert [row.requirement_code for row in result.requirements] == [
        "Y3",
        "Y1",
        "Y2",
    ]
    assert [row.requirement_text for row in result.requirements] == [
        "Requirement 3",
        "Requirement 1",
        "Requirement 2",
    ]
    assert [row.topic_name for row in result.requirements] == [
        "Topic 1",
        "Topic 1",
        "Topic 2",
    ]


# R55C4C14_HUMAN_READABLE_RECOMMENDATION_UI
