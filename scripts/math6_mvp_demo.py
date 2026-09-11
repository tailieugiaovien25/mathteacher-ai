"""Run the credential-free Mathematics 6 MVP vertical slice locally."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from assessment_generation_v2.services.math6_mvp_workflow import (  # noqa: E402
    ADMIN,
    InMemoryMath6MvpWorkflow,
)


def build_demo_package() -> bytes:
    workflow = InMemoryMath6MvpWorkflow()
    workflow.import_questions(
        (
            {
                "question_code": "M6-NAT-001",
                "stem": "Tính 27 + 35.",
                "answer": "62",
                "score": "1",
                "topic_code": "M6-NATURAL-NUMBERS",
                "cognitive_level": "KNOW",
            },
            {
                "question_code": "M6-NAT-002",
                "stem": "Tìm x biết x - 18 = 24.",
                "answer": "x = 42",
                "score": "1",
                "topic_code": "M6-NATURAL-NUMBERS",
                "cognitive_level": "UNDERSTAND",
            },
        )
    )
    workflow.edit_question(
        "M6-NAT-002",
        stem="Tìm số tự nhiên x biết x - 18 = 24.",
    )
    for code in ("M6-NAT-001", "M6-NAT-002"):
        workflow.submit_question(code)
        workflow.review_question(code, role=ADMIN, approve=True)
        workflow.lock_question(code, role=ADMIN)

    workflow.create_blueprint(
        blueprint_code="M6-DEMO-BP-001",
        title="Ma trận minh họa Toán 6",
        question_count=2,
        total_score="2",
        topic_codes=("M6-NATURAL-NUMBERS",),
    )
    workflow.submit_blueprint("M6-DEMO-BP-001")
    workflow.review_blueprint(
        "M6-DEMO-BP-001", role=ADMIN, approve=True
    )

    workflow.generate_exam(
        exam_code="M6-DEMO-001",
        title="Đề minh họa Toán 6",
        blueprint_code="M6-DEMO-BP-001",
    )
    workflow.submit_exam("M6-DEMO-001")
    workflow.review_exam("M6-DEMO-001", role=ADMIN, approve=True)
    workflow.publish_exam(
        "M6-DEMO-001", role=ADMIN, variant_code="101"
    )
    return workflow.export_zip("M6-DEMO-001")


def main() -> None:
    output_directory = PROJECT_ROOT / "output" / "math6_mvp"
    output_directory.mkdir(parents=True, exist_ok=True)
    output_file = output_directory / "math6-mvp-demo.zip"
    output_file.write_bytes(build_demo_package())
    print(f"PASS: {output_file}")


if __name__ == "__main__":
    main()
