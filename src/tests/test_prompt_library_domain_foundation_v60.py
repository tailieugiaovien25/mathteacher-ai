from dataclasses import replace

import pytest

from prompt_library_v2 import (
    PromptLifecycle,
    PromptLibraryService,
    PromptProductType,
    PromptRenderError,
)
from prompt_library_v2.defaults import default_math_prompts


def test_default_math_library_has_four_active_product_folders():
    prompts = default_math_prompts()
    assert len(prompts) == 4
    assert {item.folder.product_type for item in prompts} == set(PromptProductType)
    assert all(item.folder.subject_ref == "MATH" for item in prompts)
    assert all(item.lifecycle is PromptLifecycle.ACTIVE for item in prompts)
    assert all(item.source_path and item.source_path.is_file() for item in prompts)


def test_active_prompt_can_be_rendered_without_unresolved_variables():
    service = PromptLibraryService(default_math_prompts())
    prompt = service.find_active(
        subject_ref="MATH",
        product_type=PromptProductType.LESSON_PLAN,
    )[0]
    result = service.render(
        prompt,
        {
            "grade_level": "6",
            "subject_component": "Sá»‘ vÃ  Äáº¡i sá»‘",
            "lesson_or_topic": "PhÃ¢n sá»‘",
            "learning_requirements": "Nháº­n biáº¿t vÃ  so sÃ¡nh phÃ¢n sá»‘",
            "additional_requirements": "TÄƒng cÆ°á»ng hoáº¡t Ä‘á»™ng nhÃ³m",
        },
    )
    assert result.prompt_id == "MATH_LESSON_PLAN_V1"
    assert "PhÃ¢n sá»‘" in result.content
    assert "{{" not in result.content


def test_missing_required_input_is_rejected():
    service = PromptLibraryService(default_math_prompts())
    prompt = service.active_prompts()[0]
    with pytest.raises(PromptRenderError, match="Khá»‘i lá»›p"):
        service.render(prompt, {})


def test_user_cannot_render_non_active_prompt():
    prompt = replace(default_math_prompts()[0], lifecycle=PromptLifecycle.DRAFT)
    with pytest.raises(PromptRenderError, match="ACTIVE"):
        PromptLibraryService((prompt,)).render(prompt, {})


def test_prompt_lifecycle_is_strict_and_admin_reviewable():
    service = PromptLibraryService(default_math_prompts())
    draft = replace(service.prompts[0], lifecycle=PromptLifecycle.DRAFT)
    review = service.transition(draft, PromptLifecycle.REVIEW)
    active = service.transition(review, PromptLifecycle.ACTIVE)
    retired = service.transition(active, PromptLifecycle.RETIRED)
    assert retired.lifecycle is PromptLifecycle.RETIRED
    with pytest.raises(ValueError, match="Invalid"):
        service.transition(retired, PromptLifecycle.ACTIVE)
