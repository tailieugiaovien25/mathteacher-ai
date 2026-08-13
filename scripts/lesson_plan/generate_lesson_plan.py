"""Generate a structured lesson-plan JSON file from command-line input."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from intelligence.lesson_plan_builder import LessonPlanBuilder
from intelligence.lesson_plan_content_enricher import LessonPlanContentEnricher
from models.lesson_model import LessonModel
from models.math_lesson_plan_schema import create_math_lesson_plan_schema


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tạo khung kế hoạch bài dạy và xuất ra JSON.",
    )
    parser.add_argument("--lesson-name", required=True, help="Tên bài học.")
    parser.add_argument("--grade", required=True, help="Lớp, ví dụ: 6.")
    parser.add_argument("--subject", default="Toán", help="Môn học.")
    parser.add_argument(
        "--periods",
        type=int,
        default=1,
        help="Số tiết của bài học.",
    )
    parser.add_argument(
        "--requirement",
        action="append",
        required=True,
        help="Yêu cầu cần đạt; có thể dùng nhiều lần.",
    )
    parser.add_argument(
        "--teacher-resource",
        action="append",
        default=[],
        help="Thiết bị/học liệu của giáo viên; có thể dùng nhiều lần.",
    )
    parser.add_argument(
        "--student-resource",
        action="append",
        default=[],
        help="Học liệu của học sinh; có thể dùng nhiều lần.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Đường dẫn tệp JSON đầu ra.",
    )
    return parser


def generate_lesson_plan(args: argparse.Namespace) -> dict[str, object]:
    if args.periods < 1:
        raise ValueError("Số tiết phải lớn hơn hoặc bằng 1.")

    lesson = LessonModel(
        subject=args.subject.strip(),
        grade=args.grade.strip(),
        lesson_name=args.lesson_name.strip(),
        period_count=args.periods,
        learning_requirements=[
            item.strip() for item in args.requirement if item.strip()
        ],
        registered_equipment=[
            item.strip() for item in args.teacher_resource if item.strip()
        ],
        learning_resources=[
            item.strip() for item in args.student_resource if item.strip()
        ],
        source_file="command_line",
        source_sheet="manual_input",
    )

    if not lesson.subject or not lesson.grade or not lesson.lesson_name:
        raise ValueError("Môn, lớp và tên bài học không được để trống.")
    if not lesson.learning_requirements:
        raise ValueError("Phải có ít nhất một yêu cầu cần đạt.")

    plan = LessonPlanBuilder().build(
        lesson=lesson,
        schema=create_math_lesson_plan_schema(),
    )
    plan = LessonPlanContentEnricher().enrich(plan)
    return asdict(plan)


def write_json(data: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        plan = generate_lesson_plan(args)
        write_json(plan, args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print(f"Đã tạo kế hoạch bài dạy: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
