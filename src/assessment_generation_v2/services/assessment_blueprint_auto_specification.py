"""Produce a reviewable blueprint proposal from canonical curriculum and a profile."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Sequence

from assessment_generation_v2.services.assessment_matrix_cell_authoring import (
    AssessmentMatrixCell,
    AssessmentProfileSectionOption,
    CognitiveLevelOption,
    ProfileLevelAllocation,
    build_default_matrix_cells,
    validate_matrix_cells,
)
from assessment_generation_v2.services.blueprint_requirement_link_service import (
    BlueprintRequirementAssignment,
)


class AutoSpecificationError(ValueError):
    """The selected curriculum cannot be allocated under this profile."""


@dataclass(frozen=True)
class AutoSpecificationProposal:
    cells: tuple[AssessmentMatrixCell, ...]
    assignments: tuple[BlueprintRequirementAssignment, ...]


def propose_specification(
    *,
    sections: Sequence[AssessmentProfileSectionOption],
    cognitive_levels: Sequence[CognitiveLevelOption],
    level_allocations: Sequence[ProfileLevelAllocation],
    topic_codes: Sequence[str],
    requirement_topics: Mapping[str, str],
    existing_cells: Sequence[AssessmentMatrixCell] = (),
) -> AutoSpecificationProposal:
    """Allocate every selected requirement to at least one whole question.

    Each requirement receives a total target score equal to its allocated
    question count times its fixed per-question score. Nothing is persisted.
    """
    topics = tuple(dict.fromkeys(str(code).strip().upper() for code in topic_codes))
    if not topics or not requirement_topics:
        raise AutoSpecificationError("Hãy chọn chủ đề và YCCĐ trước khi tạo gợi ý.")
    if not existing_cells:
        try:
            cells = build_default_matrix_cells(
                sections=sections, topic_codes=topics,
                cognitive_levels=cognitive_levels, level_allocations=level_allocations,
            )
        except ValueError as exc:
            raise AutoSpecificationError(
                "Không thể chia đúng số câu và điểm của hồ sơ; hãy chỉnh ô ma trận trước."
            ) from exc
    else:
        cells = tuple(existing_cells)
        validate_matrix_cells(
            cells=cells, sections=sections,
            cognitive_levels=cognitive_levels, level_allocations=level_allocations,
        )
    if any(cell.topic_code not in topics for cell in cells):
        raise AutoSpecificationError("Ô ma trận chứa chủ đề ngoài phạm vi đã chọn.")

    codes_by_topic: dict[str, list[str]] = defaultdict(list)
    for code, topic in requirement_topics.items():
        normalized_code, normalized_topic = str(code).strip(), str(topic).strip().upper()
        if not normalized_code or normalized_topic not in topics:
            raise AutoSpecificationError("YCCĐ không thuộc chủ đề đã chọn.")
        codes_by_topic[normalized_topic].append(normalized_code)

    slots_by_topic: dict[str, list[Decimal]] = defaultdict(list)
    for cell in cells:
        score = cell.target_score / cell.question_count
        if score.as_tuple().exponent < -6:
            raise AutoSpecificationError("Điểm mỗi câu cần có tối đa 6 chữ số thập phân.")
        slots_by_topic[cell.topic_code].extend([score] * cell.question_count)

    assignments: list[BlueprintRequirementAssignment] = []
    for topic in topics:
        codes = codes_by_topic[topic]
        slots = slots_by_topic[topic]
        if not codes and slots:
            raise AutoSpecificationError(f"Chủ đề {topic} có câu hỏi nhưng chưa chọn YCCĐ.")
        if len(codes) > len(slots):
            raise AutoSpecificationError(
                f"Chủ đề {topic} có {len(codes)} YCCĐ nhưng chỉ có {len(slots)} câu."
            )
        # Give each selected requirement a slot first, then distribute the rest
        # only among requirements with the same per-question score.
        distinct_scores = tuple(dict.fromkeys(slots))
        if len(distinct_scores) > len(codes):
            raise AutoSpecificationError(
                f"Chủ đề {topic} cần thêm YCCĐ cho từng mức điểm/câu."
            )
        initial = list(distinct_scores)
        remaining = list(slots)
        for score in initial:
            remaining.remove(score)
        while len(initial) < len(codes):
            initial.append(remaining.pop(0))
        owned: dict[str, list[Decimal]] = {code: [score] for code, score in zip(codes, initial)}
        for score in remaining:
            matching = [code for code in codes if owned[code][0] == score]
            if not matching:
                raise AutoSpecificationError(
                    f"Chủ đề {topic} có mức điểm/câu chưa được gán cho YCCĐ."
                )
            chosen = min(matching, key=lambda code: (len(owned[code]), codes.index(code)))
            owned[chosen].append(score)
        for code in codes:
            assignments.append(BlueprintRequirementAssignment(
                requirement_code=code, coverage_role="PRIMARY",
                target_question_count=len(owned[code]),
                target_score=owned[code][0] * len(owned[code]),
                sequence_number=(len(assignments) + 1) * 10,
            ))
    return AutoSpecificationProposal(cells=cells, assignments=tuple(assignments))
