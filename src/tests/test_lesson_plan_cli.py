import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts/lesson_plan/generate_lesson_plan.py"


def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=PROJECT_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_cli_generates_utf8_lesson_plan_json(tmp_path):
    output = tmp_path / "lesson-plan.json"

    result = run_cli(
        "--lesson-name",
        "Phân số với tử và mẫu là số nguyên",
        "--grade",
        "6",
        "--periods",
        "2",
        "--requirement",
        "Nhận biết được phân số với tử và mẫu là số nguyên.",
        "--teacher-resource",
        "Máy chiếu",
        "--student-resource",
        "Vở ghi",
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["subject"] == "Toán"
    assert data["grade"] == "6"
    assert data["total_periods"] == 2
    assert data["objectives"]["knowledge"] == [
        "Nhận biết được phân số với tử và mẫu là số nguyên."
    ]
    assert data["resources"]["teacher"] == ["Máy chiếu"]
    assert data["resources"]["students"] == ["Vở ghi"]
    assert len(data["activities"]) == 4
    assert data["metadata"]["schema_id"] == "math_lesson_plan_v1_1"


def test_cli_rejects_non_positive_period_count(tmp_path):
    result = run_cli(
        "--lesson-name",
        "Bài mẫu",
        "--grade",
        "6",
        "--periods",
        "0",
        "--requirement",
        "Yêu cầu mẫu",
        "--output",
        str(tmp_path / "lesson-plan.json"),
    )

    assert result.returncode != 0
    assert "Số tiết phải lớn hơn hoặc bằng 1" in result.stderr
