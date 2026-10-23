from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import AIActionClass


class AISkillDomain(str, Enum):
    DOCUMENT = "document"
    LESSON = "lesson"
    ASSESSMENT = "assessment"
    CLASSROOM = "classroom"
    SYSTEM_ADMIN = "system_admin"
    MARKETING = "marketing"
    KNOWLEDGE = "knowledge"
    STUDENT = "student"


@dataclass(frozen=True)
class AISkillSpec:
    skill_id: str
    label: str
    domain: AISkillDomain
    capabilities: tuple[str, ...]
    allowed_actions: frozenset[AIActionClass]
    admin_enabled: bool = True
    description: str = ""


def default_ai_skills() -> tuple[AISkillSpec, ...]:
    """Stable skill contract; data/configuration may enable/disable skills."""
    return (
        AISkillSpec(
            "document.standardization.audit",
            "Kiá»ƒm Ä‘á»‹nh chuáº©n hÃ³a giÃ¡o Ã¡n",
            AISkillDomain.DOCUMENT,
            ("document", "vietnamese", "reasoning"),
            frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            description="PhÃ¢n tÃ­ch báº±ng chá»©ng hÃ¬nh thá»©c cá»§a DOCX; khÃ´ng sá»­a file.",
        ),
        AISkillSpec(
            "document.standardization.operator",
            "Thá»±c thi chuáº©n hÃ³a DOCX cÃ³ kiá»ƒm soÃ¡t",
            AISkillDomain.DOCUMENT,
            ("document", "standardization", "vietnamese"),
            frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY, AIActionClass.MUTATING}),
            description="Cho phÃ©p thá»±c thi transformer deterministic sau khi ADMIN phÃª duyá»‡t thao tÃ¡c thay Ä‘á»•i.",
        ),
        AISkillSpec(
            "lesson.authoring.assistant",
            "Trá»£ lÃ½ thiáº¿t káº¿ giÃ¡o Ã¡n",
            AISkillDomain.LESSON,
            ("general", "vietnamese", "lesson"),
            frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            description="Há»— trá»£ xÃ¢y dá»±ng ná»™i dung bÃ i dáº¡y vÃ  hoáº¡t Ä‘á»™ng.",
        ),
        AISkillSpec(
            "assessment.reasoning",
            "Trá»£ lÃ½ kiá»ƒm tra â€“ Ä‘Ã¡nh giÃ¡",
            AISkillDomain.ASSESSMENT,
            ("vietnamese", "mathematics", "reasoning"),
            frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            description="PhÃ¢n tÃ­ch ma tráº­n, Ä‘áº·c táº£, cÃ¢u há»i vÃ  Ä‘Ã¡p Ã¡n.",
        ),
        AISkillSpec(
            "student.self_learning",
            "Tá»± há»c ToÃ¡n",
            AISkillDomain.STUDENT,
            ("general", "vietnamese", "mathematics", "pedagogy"),
            frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            description="Trá»£ lÃ½ há»c táº­p ToÃ¡n theo hÆ°á»›ng gá»£i má»Ÿ, Æ°u tiÃªn hÆ°á»›ng dáº«n tá»«ng bÆ°á»›c vÃ  phÃ¢n tÃ­ch lá»—i thay vÃ¬ giáº£i há»™ ngay.",
        ),        AISkillSpec(
            "classroom.assistant",
            "Trá»£ lÃ½ lá»›p há»c",
            AISkillDomain.CLASSROOM,
            ("general", "vietnamese", "agentic"),
            frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            description="Há»— trá»£ váº­n hÃ nh hoáº¡t Ä‘á»™ng lá»›p há»c theo dá»¯ liá»‡u Ä‘Ã£ Ä‘Æ°á»£c phÃ©p.",
        ),
        AISkillSpec(
            "classroom.teaching.orchestrator",
            "Äiá»u phá»‘i trá»£ giáº£ng lá»›p há»c",
            AISkillDomain.CLASSROOM,
            ("classroom", "vietnamese", "mc", "activity_facilitation"),
            frozenset({
                AIActionClass.READ_ONLY,
                AIActionClass.ADVISORY,
                AIActionClass.MUTATING,
            }),
            description=(
                "Láº­p ká»‹ch báº£n MC vÃ  káº¿ hoáº¡ch Ä‘iá»u phá»‘i hoáº¡t Ä‘á»™ng; thao tÃ¡c lá»›p há»c "
                "cÃ³ side effect pháº£i qua xÃ¡c nháº­n cá»§a giÃ¡o viÃªn/ADMIN theo policy."
            ),
        ),
        AISkillSpec(
            "system_admin.observer",
            "AI Quáº£n trá»‹ há»‡ thá»‘ng",
            AISkillDomain.SYSTEM_ADMIN,
            ("general", "reasoning", "coding"),
            frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            description="Quan sÃ¡t, phÃ¢n tÃ­ch vÃ  Ä‘á» xuáº¥t; thao tÃ¡c production cáº§n ADMIN duyá»‡t.",
        ),
        AISkillSpec(
            "marketing.assistant",
            "AI Marketing",
            AISkillDomain.MARKETING,
            ("general", "vietnamese", "reasoning"),
            frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            admin_enabled=False,
            description="Táº¡o báº£n nhÃ¡p marketing; máº·c Ä‘á»‹nh khÃ³a Ä‘áº¿n giai Ä‘oáº¡n thÆ°Æ¡ng máº¡i.",
        ),
        AISkillSpec(
            "knowledge.curator",
            "Quáº£n trá»‹ tri thá»©c AI",
            AISkillDomain.KNOWLEDGE,
            ("general", "document", "vietnamese"),
            frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            description="Chuáº©n bá»‹ candidate knowledge; phÃ¡t hÃ nh tri thá»©c cáº§n ADMIN duyá»‡t.",
        ),
    )
