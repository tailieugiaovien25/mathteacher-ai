from models.lesson_model import LessonModel
from models.lesson_plan_content import (
    LearningActivity,
    LessonObjectives,
    LessonPlanContent,
    TeachingResources,
)
from models.lesson_plan_schema import LessonPlanSchema


class LessonPlanBuilder:
    """Tạo khung giáo án từ LessonModel và LessonPlanSchema."""

    def build(
        self,
        lesson: LessonModel,
        schema: LessonPlanSchema,
    ) -> LessonPlanContent:
        activities = [
            LearningActivity(
                key=activity_schema.key,
                title=activity_schema.title,
                organization_layout=(
                    activity_schema.default_layout
                ),
            )
            for activity_schema in schema.activities
        ]

        return LessonPlanContent(
            subject=lesson.subject,
            grade=lesson.grade,
            lesson_name=lesson.lesson_name,
            total_periods=lesson.period_count or 1,
            objectives=LessonObjectives(
                knowledge=list(
                    lesson.learning_requirements
                ),
            ),
            resources=TeachingResources(
                teacher=list(
                    lesson.registered_equipment
                ),
                students=list(
                    lesson.learning_resources
                ),
            ),
            activities=activities,
            metadata={
                "schema_id": schema.schema_id,
                "schema_version": schema.version,
                "source_file": lesson.source_file,
                "source_sheet": lesson.source_sheet,
                "source_row": lesson.source_row,
            },
        )