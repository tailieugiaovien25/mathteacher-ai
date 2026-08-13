"""Command-line entry point for Lesson Plan Word Standardizer V1."""

from __future__ import annotations

import argparse
from pathlib import Path

from document_standardization import LessonPlanWordStandardizer


def main() -> int:
    parser = argparse.ArgumentParser(description="Chuẩn hóa hình thức kế hoạch bài dạy Word mà không ghi đè bản gốc.")
    parser.add_argument("input", type=Path, help="Tệp DOCX gốc.")
    parser.add_argument("--profile", type=Path, default=Path(__file__).with_name("lesson_plan_profile.json"))
    parser.add_argument("--output", type=Path, help="Tệp DOCX đã chuẩn hóa.")
    parser.add_argument("--report", type=Path, help="Báo cáo JSON.")
    args = parser.parse_args()
    output = args.output or args.input.with_name(args.input.stem + ".standardized.docx")
    report = args.report or args.input.with_name(args.input.stem + ".standardization-report.json")
    result = LessonPlanWordStandardizer.from_json(args.profile).standardize(args.input, output, report)
    print(f"Đã tạo bản chuẩn hóa: {output}")
    print(f"Đã tạo báo cáo: {report}")
    print(f"Kết quả: {result['result']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
