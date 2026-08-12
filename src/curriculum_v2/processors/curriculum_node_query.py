from __future__ import annotations

import json
from pathlib import Path

from curriculum_v2.models.curriculum_node import CurriculumNode


class CurriculumNodeQuery:
    """Read-only query and hierarchy service for canonical curriculum nodes."""

    VALID_GRADES = {6, 7, 8, 9}

    def __init__(self, canonical_root: str | Path | None = None) -> None:
        if canonical_root is None:
            canonical_root = (
                Path(__file__).resolve().parents[1]
                / "data"
                / "canonical"
                / "mathematics"
            )
        self.canonical_root = Path(canonical_root)

    @classmethod
    def _validate_grade(cls, grade: int) -> None:
        if grade not in cls.VALID_GRADES:
            raise ValueError("grade must be one of 6, 7, 8, 9")

    def _nodes_file(self, grade: int) -> Path:
        self._validate_grade(grade)
        return (
            self.canonical_root
            / f"grade_{grade:02d}"
            / "curriculum_nodes.json"
        )

    def by_grade(self, grade: int) -> list[CurriculumNode]:
        path = self._nodes_file(grade)
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        curriculum_ref = data["curriculum_ref"]
        return [
            CurriculumNode(
                curriculum_node_id=item["curriculum_node_id"],
                curriculum_ref=curriculum_ref,
                code=item["code"],
                name=item["name"],
                node_type=item["node_type"],
                parent_id=item.get("parent_id"),
                sequence=item.get("sequence", 0),
                status=item.get("status", "ACTIVE"),
                metadata=item.get("metadata", {}),
            )
            for item in data["nodes"]
        ]

    def by_id(self, curriculum_node_id: str) -> CurriculumNode | None:
        for grade in (6, 7, 8, 9):
            for node in self.by_grade(grade):
                if node.curriculum_node_id == curriculum_node_id:
                    return node
        return None

    def roots(self, grade: int) -> list[CurriculumNode]:
        return [
            node for node in self.by_grade(grade)
            if node.parent_id is None
        ]

    def children(
        self,
        grade: int,
        parent_id: str,
    ) -> list[CurriculumNode]:
        return sorted(
            [
                node for node in self.by_grade(grade)
                if node.parent_id == parent_id
            ],
            key=lambda node: node.sequence,
        )

    def descendants(
        self,
        grade: int,
        node_id: str,
    ) -> list[CurriculumNode]:
        nodes = self.by_grade(grade)
        by_parent: dict[str | None, list[CurriculumNode]] = {}

        for node in nodes:
            by_parent.setdefault(node.parent_id, []).append(node)

        for children in by_parent.values():
            children.sort(key=lambda node: node.sequence)

        results: list[CurriculumNode] = []

        def walk(parent_id: str) -> None:
            for child in by_parent.get(parent_id, []):
                results.append(child)
                walk(child.curriculum_node_id)

        walk(node_id)
        return results

    def ancestors(
        self,
        grade: int,
        node_id: str,
    ) -> list[CurriculumNode]:
        nodes = self.by_grade(grade)
        by_id = {node.curriculum_node_id: node for node in nodes}

        current = by_id.get(node_id)
        if current is None:
            return []

        results: list[CurriculumNode] = []
        parent_id = current.parent_id

        while parent_id is not None:
            parent = by_id.get(parent_id)
            if parent is None:
                break
            results.append(parent)
            parent_id = parent.parent_id

        results.reverse()
        return results

    def search(
        self,
        keyword: str,
        *,
        grade: int | None = None,
    ) -> list[CurriculumNode]:
        keyword = keyword.strip()
        if not keyword:
            return []

        grades = (grade,) if grade is not None else (6, 7, 8, 9)
        needle = keyword.casefold()
        results: list[CurriculumNode] = []

        for current_grade in grades:
            self._validate_grade(current_grade)
            for node in self.by_grade(current_grade):
                if (
                    needle in node.name.casefold()
                    or needle in node.code.casefold()
                ):
                    results.append(node)

        return results


def get_curriculum_node_query() -> CurriculumNodeQuery:
    return CurriculumNodeQuery()
