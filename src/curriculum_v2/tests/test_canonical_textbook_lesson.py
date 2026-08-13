from curriculum_v2.textbooks import (
    CanonicalTextbookLesson,
    TextbookLessonProvenance,
)


def expect_error(error_type, action):
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False

    return False


def make_provenance():
    return TextbookLessonProvenance(
        source_document_id="SRC-TB-MATH6-KNTT",
        publisher="NXB Giáo dục Việt Nam",
        source_location="Bài 1",
        source_version="2026",
    )


def make_lesson():
    return CanonicalTextbookLesson(
        lesson_id="TB-MATH6-KNTT-L001",
        textbook_ref="TEXTBOOK-MATH6-KNTT",
        subject="Toán",
        grade=6,
        title="Bài 1. Tập hợp",
        sequence=1,
        provenance=make_provenance(),
        lesson_kind="lesson",
        unit_ref="CHAPTER-01",
        unit_title="Số tự nhiên",
        status="verified",
    )


def main():
    print("=" * 72)
    print(
        "WR-001D.6 - CANONICAL TEXTBOOK "
        "LESSON CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    lesson = make_lesson()

    checks = [
        (
            "CTL1 Valid lesson accepted",
            lesson.grade == 6,
        ),
        (
            "CTL2 Text fields normalized",
            lesson.title == "Bài 1. Tập hợp",
        ),
        (
            "CTL3 Status normalized",
            lesson.status == "VERIFIED",
        ),
        (
            "CTL4 Lesson kind normalized",
            lesson.lesson_kind == "LESSON",
        ),
        (
            "CTL5 Provenance preserved",
            (
                lesson.provenance.source_document_id
                == "SRC-TB-MATH6-KNTT"
            ),
        ),
        (
            "CTL6 Empty lesson ID blocked",
            expect_error(
                ValueError,
                lambda: CanonicalTextbookLesson(
                    lesson_id="   ",
                    textbook_ref="TEXTBOOK-MATH6-KNTT",
                    subject="Toán",
                    grade=6,
                    title="Bài 1",
                    sequence=1,
                    provenance=make_provenance(),
                ),
            ),
        ),
        (
            "CTL7 Invalid grade blocked",
            expect_error(
                ValueError,
                lambda: CanonicalTextbookLesson(
                    lesson_id="L1",
                    textbook_ref="TB1",
                    subject="Toán",
                    grade=0,
                    title="Bài 1",
                    sequence=1,
                    provenance=make_provenance(),
                ),
            ),
        ),
        (
            "CTL8 Invalid sequence blocked",
            expect_error(
                ValueError,
                lambda: CanonicalTextbookLesson(
                    lesson_id="L1",
                    textbook_ref="TB1",
                    subject="Toán",
                    grade=6,
                    title="Bài 1",
                    sequence=0,
                    provenance=make_provenance(),
                ),
            ),
        ),
        (
            "CTL9 Invalid provenance blocked",
            expect_error(
                TypeError,
                lambda: CanonicalTextbookLesson(
                    lesson_id="L1",
                    textbook_ref="TB1",
                    subject="Toán",
                    grade=6,
                    title="Bài 1",
                    sequence=1,
                    provenance="invalid",
                ),
            ),
        ),
        (
            "CTL10 Invalid status blocked",
            expect_error(
                ValueError,
                lambda: CanonicalTextbookLesson(
                    lesson_id="L1",
                    textbook_ref="TB1",
                    subject="Toán",
                    grade=6,
                    title="Bài 1",
                    sequence=1,
                    provenance=make_provenance(),
                    status="UNKNOWN",
                ),
            ),
        ),
    ]

    for label, passed in checks:
        results.append(passed)

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    immutable = False

    try:
        lesson.title = "Changed"
    except Exception:
        immutable = True

    results.append(immutable)

    print(
        "CTL11 Lesson immutable: "
        f"{'PASS' if immutable else 'FAIL'}"
    )

    provenance_immutable = False

    try:
        lesson.provenance.publisher = "Changed"
    except Exception:
        provenance_immutable = True

    results.append(provenance_immutable)

    print(
        "CTL12 Provenance immutable: "
        f"{'PASS' if provenance_immutable else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - "
            "CANONICAL TEXTBOOK LESSON "
            "CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - "
            "CANONICAL TEXTBOOK LESSON "
            "CONTRACT VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
