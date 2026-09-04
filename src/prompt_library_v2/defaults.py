from pathlib import Path

from .models import (
    PromptFolder,
    PromptLifecycle,
    PromptProductType,
    PromptTemplate,
    PromptVariable,
)
from .service import read_prompt_file


ROOT = Path(__file__).resolve().parent / "prompts" / "math"

COMMON_VARIABLES = (
    PromptVariable("grade_level", "Khá»‘i lá»›p"),
    PromptVariable("subject_component", "Máº¡ch ná»™i dung/phÃ¢n mÃ´n"),
    PromptVariable("lesson_or_topic", "BÃ i há»c/chá»§ Ä‘á»"),
    PromptVariable("learning_requirements", "YÃªu cáº§u cáº§n Ä‘áº¡t"),
    PromptVariable("additional_requirements", "YÃªu cáº§u bá»• sung", required=False),
)


def _folder(folder_id: str, label: str, product_type: PromptProductType) -> PromptFolder:
    return PromptFolder(
        folder_id=folder_id,
        label=label,
        product_type=product_type,
        subject_ref="MATH",
    )


def default_math_prompts() -> tuple[PromptTemplate, ...]:
    definitions = (
        ("MATH_LESSON_PLAN_V1", "Táº¡o giÃ¡o Ã¡n vá»›i Prompt", PromptProductType.LESSON_PLAN, "lesson_plan.md"),
        ("MATH_MATRIX_V1", "Táº¡o ma tráº­n ÄKT vá»›i Prompt", PromptProductType.ASSESSMENT_MATRIX, "assessment_matrix.md"),
        ("MATH_SPECIFICATION_V1", "Táº¡o báº£n Ä‘áº·c táº£ ÄKT vá»›i Prompt", PromptProductType.ASSESSMENT_SPECIFICATION, "assessment_specification.md"),
        ("MATH_EXAM_V1", "Táº¡o ÄKT vá»›i Prompt", PromptProductType.ASSESSMENT_EXAM, "assessment_exam.md"),
    )
    result = []
    for prompt_id, label, product_type, filename in definitions:
        path = ROOT / filename
        result.append(
            PromptTemplate(
                prompt_id=prompt_id,
                folder=_folder(prompt_id.lower(), label, product_type),
                name=label,
                version=1,
                lifecycle=PromptLifecycle.ACTIVE,
                content=read_prompt_file(path),
                variables=COMMON_VARIABLES,
                source_path=path,
            )
        )
    return tuple(result)
