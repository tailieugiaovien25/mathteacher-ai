from enum import Enum


class LessonPlanSelectionMode(str, Enum):
    """
    Canonical lesson-plan working-unit selection mode.

    This enum is shared by:
    - subject lesson-plan profiles
    - unit selection services
    - portal UI
    """

    LESSON = "lesson"
    PERIOD = "period"
    TOPIC = "topic"
    WEEK_SUBJECT = "week_subject"
