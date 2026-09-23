"""Deterministic draft blueprint allocation from governed policy data.

Profiles describe sections and score targets; curated eligibility says which
YCCĐ supports each (section, cognitive level). No grade-specific rules live here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Sequence


class AutoBlueprintError(ValueError):
    """No safe exact allocation exists for the selected profile and YCCĐ."""


@dataclass(frozen=True)
class PlannedCell:
    sequence_number: int
    topic_code: str
    section_code: str
    question_type_code: str
    cognitive_level_code: str
    question_count: int
    response_count: int
    target_score: Decimal
    requirement_codes: tuple[str, ...]


def plan_blueprint(
    *,
    sections: Sequence[Mapping[str, object]],
    cognitive_targets: Mapping[str, Decimal],
    requirements: Sequence[Mapping[str, object]],
    total_score: Decimal,
) -> tuple[PlannedCell, ...]:
    """Propose a draft allocation; ambiguous or unsupported coverage fails closed.

    Eligibility is an admin curated list of ``[section_code, level_code]``
    pairs per requirement. It must come from reviewed data, not inferred from
    wording or AI output. Each selected requirement is covered at least once.
    """
    if not sections or not requirements or not cognitive_targets:
        raise AutoBlueprintError("Profile, level targets and reviewed YCCĐ are required")
    target = {str(k): Decimal(str(v)) for k, v in cognitive_targets.items()}
    if any(v < 0 for v in target.values()) or sum(target.values(), Decimal(0)) != total_score:
        raise AutoBlueprintError("Cognitive targets do not match profile score")
    if sum((Decimal(str(s['section_score'])) for s in sections), Decimal(0)) != total_score:
        raise AutoBlueprintError("Section scores do not match profile score")
    codes = [str(r['requirement_code']) for r in requirements]
    if len(set(codes)) != len(codes):
        raise AutoBlueprintError("Duplicate YCCĐ")
    normalized: dict[str, tuple[str, frozenset[tuple[str, str]]]] = {}
    for requirement in requirements:
        code = str(requirement['requirement_code'])
        topic = str(requirement['topic_code'])
        eligibility = requirement.get('eligibility')
        if not code or not topic or not isinstance(eligibility, (list, tuple)) or not eligibility:
            raise AutoBlueprintError(f"Missing curated eligibility for {code}")
        pairs = frozenset((str(p[0]), str(p[1])) for p in eligibility)
        normalized[code] = (topic, pairs)

    # Represent each question as one indivisible slot. Try valid level and
    # YCCĐ placements via deterministic backtracking; exact totals are required.
    slots: list[tuple[str, str, Decimal, int]] = []
    for section in sections:
        count = int(section['question_count'])
        responses = int(section['response_count'])
        score = Decimal(str(section['section_score']))
        if count <= 0 or responses < count or score <= 0 or responses % count:
            raise AutoBlueprintError("Section cannot be divided into exact question slots")
        for _ in range(count):
            slots.append((str(section['section_code']), str(section['question_type_code']),
                          score / count, responses // count))
    topics = {topic for topic, _ in normalized.values()}
    if len(slots) < len(topics):
        raise AutoBlueprintError("Profile has fewer questions than selected topics")
    allocations: list[tuple[str, str]] = []
    used = Counter()

    def assign(index: int) -> bool:
        if index == len(slots):
            return (all(v == 0 for v in target.values())
                    and {normalized[c][0] for c in codes if used[c]} == topics
                    and (len(codes) > len(slots) or all(used[c] for c in codes)))
        section, _, score, _ = slots[index]
        # Prefer uncovered topics, then requirements, then even coverage.
        options = sorted(
            ((level, code) for level in target for code in codes
             if target[level] >= score and (section, level) in normalized[code][1]),
            key=lambda pair: (any(used[c] for c in codes if normalized[c][0] == normalized[pair[1]][0]),
                              used[pair[1]] > 0, used[pair[1]], pair[0], pair[1]),
        )
        for level, code in options:
            target[level] -= score
            used[code] += 1
            allocations.append((level, code))
            if assign(index + 1):
                return True
            allocations.pop()
            used[code] -= 1
            target[level] += score
        return False

    if not assign(0):
        raise AutoBlueprintError("No exact governed allocation covers selected YCCĐ")
    grouped: dict[tuple[str, str, str, str, Decimal, int], list[str]] = defaultdict(list)
    for (section, typ, score, responses), (level, code) in zip(slots, allocations):
        grouped[(section, typ, normalized[code][0], level, score, responses)].append(code)
    return tuple(
        PlannedCell(i, topic, section, typ, level, len(group), len(group) * response,
                    score * len(group), tuple(group))
        for i, ((section, typ, topic, level, score, response), group)
        in enumerate(grouped.items(), 1)
    )
