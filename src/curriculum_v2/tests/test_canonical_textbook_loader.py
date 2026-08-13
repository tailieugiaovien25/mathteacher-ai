from pathlib import Path

from curriculum_v2.textbooks import (
    CanonicalTextbookLesson,
)
from curriculum_v2.textbooks.processors import (
    load_canonical_textbook_lessons,
)


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "textbooks"
    / "data"
    / "mathematics"
    / "grade_06"
    / "ket_noi_tri_thuc"
    / "textbook_lessons.json"
)


def main():
    print("=" * 72)
    print(
        "WR-001D.8 - CANONICAL TEXTBOOK "
        "LOADER TEST"
    )
    print("=" * 72)

    results = []

    lessons = load_canonical_textbook_lessons(
        DATA_FILE
    )

    checks = [
        (
            "CTLDR1 Data file exists",
            DATA_FILE.exists(),
        ),
        (
            "CTLDR2 One lesson loaded",
            len(lessons) == 1,
        ),
        (
            "CTLDR3 Canonical lesson object returned",
            isinstance(
                lessons[0],
                CanonicalTextbookLesson,
            ),
        ),
        (
            "CTLDR4 Textbook ref preserved",
            lessons[0].textbook_ref
            == "TEXTBOOK-MATH6-KNTT",
        ),
        (
            "CTLDR5 Subject preserved",
            lessons[0].subject == "Toán",
        ),
        (
            "CTLDR6 Grade preserved",
            lessons[0].grade == 6,
        ),
        (
            "CTLDR7 Lesson identity preserved",
            lessons[0].lesson_id
            == "TB-MATH6-KNTT-L001",
        ),
        (
            "CTLDR8 Provenance preserved",
            lessons[0]
            .provenance
            .source_document_id
            == "SRC-TB-MATH6-KNTT",
        ),
        (
            "CTLDR9 Status preserved",
            lessons[0].status
            == "CANDIDATE",
        ),
        (
            "CTLDR10 Schema preserved",
            lessons[0].schema_version
            == 1,
        ),
    ]

    for label, passed in checks:
        results.append(passed)

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - "
            "CANONICAL TEXTBOOK LOADER VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - "
            "CANONICAL TEXTBOOK LOADER VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
