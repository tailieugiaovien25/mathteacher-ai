import json
import tempfile
from pathlib import Path

from curriculum_v2.textbooks.validators import (
    is_textbook_dataset_generation_ready,
    validate_canonical_textbook_dataset,
)


BASE = (
    Path(__file__).resolve().parents[1]
    / "textbooks"
    / "data"
)

LESSONS_FILE = (
    BASE
    / "mathematics"
    / "grade_06"
    / "ket_noi_tri_thuc"
    / "textbook_lessons.json"
)

SOURCE_FILE = (
    BASE
    / "sources"
    / "SRC-TB-MATH6-KNTT.json"
)


def main():
    print("=" * 72)
    print(
        "WR-001D.9 - CANONICAL TEXTBOOK "
        "DATASET VALIDATOR TEST"
    )
    print("=" * 72)

    results = []

    errors = (
        validate_canonical_textbook_dataset(
            LESSONS_FILE,
            SOURCE_FILE,
        )
    )

    checks = [
        (
            "CTDV1 Lessons file exists",
            LESSONS_FILE.exists(),
        ),
        (
            "CTDV2 Source registry exists",
            SOURCE_FILE.exists(),
        ),
        (
            "CTDV3 Dataset structurally valid",
            errors == [],
        ),
        (
            "CTDV4 Candidate dataset not generation-ready",
            not is_textbook_dataset_generation_ready(
                LESSONS_FILE,
                SOURCE_FILE,
            ),
        ),
    ]

    for label, passed in checks:
        results.append(passed)

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    # --------------------------------------------------------
    # Duplicate lesson ID detection
    # --------------------------------------------------------

    with LESSONS_FILE.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        raw = json.load(file)

    duplicate_data = dict(raw)
    duplicate_data["lessons"] = list(
        raw["lessons"]
    )

    duplicate_data["lessons"].append(
        dict(raw["lessons"][0])
    )

    with tempfile.TemporaryDirectory() as tmp:
        temp_path = (
            Path(tmp)
            / "duplicate_lessons.json"
        )

        with temp_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                duplicate_data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        duplicate_errors = (
            validate_canonical_textbook_dataset(
                temp_path,
                SOURCE_FILE,
            )
        )

    passed = (
        "DUPLICATE_LESSON_ID"
        in duplicate_errors
    )

    results.append(passed)

    print(
        "CTDV5 Duplicate lesson ID blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # --------------------------------------------------------
    # Unknown source detection
    # --------------------------------------------------------

    bad_source_data = dict(raw)
    bad_source_data["lessons"] = [
        dict(raw["lessons"][0])
    ]

    bad_source_data["lessons"][0] = dict(
        bad_source_data["lessons"][0]
    )

    bad_source_data["lessons"][0][
        "provenance"
    ] = dict(
        bad_source_data["lessons"][0][
            "provenance"
        ]
    )

    bad_source_data["lessons"][0][
        "provenance"
    ][
        "source_document_id"
    ] = "UNKNOWN-SOURCE"

    with tempfile.TemporaryDirectory() as tmp:
        temp_path = (
            Path(tmp)
            / "unknown_source.json"
        )

        with temp_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                bad_source_data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        source_errors = (
            validate_canonical_textbook_dataset(
                temp_path,
                SOURCE_FILE,
            )
        )

    passed = any(
        error.startswith(
            "UNKNOWN_TEXTBOOK_SOURCE:"
        )
        for error in source_errors
    )

    results.append(passed)

    print(
        "CTDV6 Unknown provenance source blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    print(
        f"STRUCTURAL ERRORS: "
        f"{len(errors)}"
    )

    print(
        "GENERATION READY: "
        f"{is_textbook_dataset_generation_ready(LESSONS_FILE, SOURCE_FILE)}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - "
            "CANONICAL TEXTBOOK DATASET "
            "VALIDATOR VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - "
            "CANONICAL TEXTBOOK DATASET "
            "VALIDATOR VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
