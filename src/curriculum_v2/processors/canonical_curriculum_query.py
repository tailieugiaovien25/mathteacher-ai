from __future__ import annotations

from pathlib import Path

from curriculum_v2.models import CanonicalLearningRequirement
from curriculum_v2.processors.canonical_requirement_loader import load_canonical_requirements


class CanonicalCurriculumQuery:
    """Read-only query layer for canonical learning requirements."""

    def __init__(self, canonical_root: str | Path | None = None) -> None:
        if canonical_root is None:
            canonical_root = Path(__file__).resolve().parents[1] / "data" / "canonical" / "mathematics"
        self.canonical_root = Path(canonical_root)

    @staticmethod
    def _validate_grade(grade: int) -> None:
        if grade not in {6, 7, 8, 9}:
            raise ValueError("grade must be one of 6, 7, 8, 9")

    def _requirements_file(self, grade: int) -> Path:
        self._validate_grade(grade)
        return self.canonical_root / f"grade_{grade:02d}" / "learning_requirements.json"

    def by_grade(self, grade: int) -> list[CanonicalLearningRequirement]:
        return load_canonical_requirements(self._requirements_file(grade))

    def by_node(self, grade: int, curriculum_node_id: str) -> list[CanonicalLearningRequirement]:
        return [r for r in self.by_grade(grade) if r.curriculum_node_ref == curriculum_node_id]

    def by_id(self, canonical_id: str) -> CanonicalLearningRequirement | None:
        for grade in (6, 7, 8, 9):
            for requirement in self.by_grade(grade):
                if requirement.canonical_id == canonical_id:
                    return requirement
        return None

    def search(self, keyword: str, *, grade: int | None = None) -> list[CanonicalLearningRequirement]:
        keyword = keyword.strip()
        if not keyword:
            return []
        grades = (grade,) if grade is not None else (6, 7, 8, 9)
        needle = keyword.casefold()
        results = []
        for current_grade in grades:
            for requirement in self.by_grade(current_grade):
                if needle in requirement.requirement_text_original.casefold():
                    results.append(requirement)
        return results


def get_canonical_curriculum_query() -> CanonicalCurriculumQuery:
    return CanonicalCurriculumQuery()
