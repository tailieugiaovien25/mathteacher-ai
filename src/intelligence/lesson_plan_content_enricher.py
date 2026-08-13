"""Enrich lesson-plan activities without subject-specific hard-coded data."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from models.lesson_plan_content import LessonPlanContent, OrganizationStep


@dataclass(frozen=True)
class ActivityContentProfile:
    objective_prefix: str
    content_template: str
    product_template: str
    steps: tuple[tuple[str, str, str], ...]


ACTIVITY_PROFILES = {
    "opening": ActivityContentProfile(
        objective_prefix="Kích hoạt kiến thức nền và xác định nhiệm vụ học tập về",
        content_template="Tình huống khởi động gắn với {lesson_name}.",
        product_template="Câu trả lời ban đầu và nhiệm vụ học tập được xác định.",
        steps=(
            ("Chuyển giao nhiệm vụ", "Giáo viên nêu tình huống; học sinh tiếp nhận nhiệm vụ.", "Nhiệm vụ được xác định."),
            ("Thực hiện nhiệm vụ", "Học sinh suy nghĩ, trao đổi và trình bày hiểu biết ban đầu.", "Ý kiến ban đầu của học sinh."),
        ),
    ),
    "knowledge_formation": ActivityContentProfile(
        objective_prefix="Hình thành kiến thức và đáp ứng yêu cầu",
        content_template="Khám phá, phân tích và khái quát nội dung của {lesson_name}.",
        product_template="Kết luận hoặc kiến thức mới phù hợp với yêu cầu cần đạt.",
        steps=(
            ("Chuyển giao nhiệm vụ", "Giáo viên giao nhiệm vụ khám phá; học sinh xác định dữ kiện và yêu cầu.", "Kế hoạch thực hiện nhiệm vụ."),
            ("Thực hiện nhiệm vụ", "Học sinh làm việc cá nhân hoặc hợp tác; giáo viên quan sát và hỗ trợ.", "Kết quả khám phá của học sinh."),
            ("Báo cáo và thảo luận", "Học sinh trình bày, phản hồi; giáo viên tổ chức trao đổi.", "Các lập luận và kết quả đã được thảo luận."),
            ("Kết luận", "Giáo viên cùng học sinh chuẩn hóa và khái quát kiến thức.", "Kết luận kiến thức của hoạt động."),
        ),
    ),
    "practice": ActivityContentProfile(
        objective_prefix="Củng cố và vận dụng trực tiếp yêu cầu",
        content_template="Bài tập hoặc nhiệm vụ luyện tập về {lesson_name}.",
        product_template="Lời giải hoặc kết quả luyện tập có giải thích.",
        steps=(
            ("Giao nhiệm vụ", "Giáo viên giao bài tập; học sinh xác định cách thực hiện.", "Phương án giải quyết."),
            ("Luyện tập", "Học sinh thực hiện và đối chiếu kết quả; giáo viên hỗ trợ khi cần.", "Kết quả luyện tập."),
            ("Đánh giá", "Học sinh tự đánh giá hoặc đánh giá đồng đẳng; giáo viên phản hồi.", "Kết quả đã được điều chỉnh."),
        ),
    ),
    "application": ActivityContentProfile(
        objective_prefix="Vận dụng kiến thức để giải quyết nhiệm vụ gắn với",
        content_template="Tình huống vận dụng hoặc mở rộng liên quan đến {lesson_name}.",
        product_template="Phương án giải quyết hoặc sản phẩm vận dụng.",
        steps=(
            ("Đề xuất nhiệm vụ", "Giáo viên giới thiệu bối cảnh; học sinh lựa chọn cách giải quyết.", "Ý tưởng vận dụng."),
            ("Thực hiện và chia sẻ", "Học sinh thực hiện, trình bày sản phẩm; giáo viên phản hồi.", "Sản phẩm vận dụng hoàn chỉnh."),
        ),
    ),
}


class LessonPlanContentEnricher:
    """Fill activity content using only the plan's supplied lesson data."""

    def enrich(self, plan: LessonPlanContent) -> LessonPlanContent:
        enriched = deepcopy(plan)
        requirements = [
            item.strip().rstrip(".;:!?")
            for item in enriched.objectives.knowledge
            if item.strip().rstrip(".;:!?")
        ]
        requirement_text = "; ".join(requirements)

        for activity in enriched.activities:
            profile = ACTIVITY_PROFILES.get(activity.key)
            if profile is None:
                continue

            focus = requirement_text or enriched.lesson_name
            activity.objective = f"{profile.objective_prefix} {focus}."
            activity.content = profile.content_template.format(
                lesson_name=enriched.lesson_name,
            )
            activity.product = profile.product_template
            activity.organization_steps = [
                OrganizationStep(
                    title=title,
                    teacher_student_activity=actions,
                    expected_product=product,
                )
                for title, actions, product in profile.steps
            ]

        enriched.metadata["content_enricher"] = "rule_based_v1"
        return enriched
