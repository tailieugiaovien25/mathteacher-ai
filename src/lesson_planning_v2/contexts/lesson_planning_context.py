from dataclasses import dataclass

from curriculum_v2.models import CanonicalLearningRequirement
from curriculum_v2.models.curriculum_node import CurriculumNode
from educational_planning_v2.models import CurriculumScope


@dataclass(frozen=True)
class LessonPlanningContext:
    """Canonical context for constructing one lesson plan."""

    educational_plan_id: str
    plan_item_id: str
    title: str

    academic_year: str
    subject: str
    grade: int
    periods: int

    curriculum_scope: CurriculumScope
    nodes: tuple[CurriculumNode, ...]
    requirements: tuple[CanonicalLearningRequirement, ...]
