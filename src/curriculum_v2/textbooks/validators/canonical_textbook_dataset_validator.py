import json
from pathlib import Path

from curriculum_v2.textbooks.processors import (
    load_canonical_textbook_lessons,
)


EXPECTED_TEXTBOOK_SCHEMA_VERSION = 1


def _load_json(
    file_path: str | Path,
) -> dict:
    path = Path(file_path)

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        return json.load(file)


def validate_canonical_textbook_dataset(
    lessons_file: str | Path,
    source_file: str | Path,
) -> list[str]:
    errors: list[str] = []

    lessons_data = _load_json(
        lessons_file
    )

    source_data = _load_json(
        source_file
    )

    lessons = load_canonical_textbook_lessons(
        lessons_file
    )

    # --------------------------------------------------------
    # 1. Schema version
    # --------------------------------------------------------

    if (
        lessons_data.get("schema_version")
        != EXPECTED_TEXTBOOK_SCHEMA_VERSION
    ):
        errors.append(
            "INVALID_TEXTBOOK_SCHEMA_VERSION"
        )

    # --------------------------------------------------------
    # 2. Source identity
    # --------------------------------------------------------

    source_id = source_data.get(
        "source_id"
    )

    if not isinstance(source_id, str) or not source_id.strip():
        errors.append(
            "INVALID_SOURCE_ID"
        )

    # --------------------------------------------------------
    # 3. Dataset ↔ source identity consistency
    # --------------------------------------------------------

    if (
        lessons_data.get("textbook_ref")
        != source_data.get("textbook_ref")
    ):
        errors.append(
            "TEXTBOOK_REF_SOURCE_MISMATCH"
        )

    if (
        lessons_data.get("subject")
        != source_data.get("subject")
    ):
        errors.append(
            "SUBJECT_SOURCE_MISMATCH"
        )

    if (
        lessons_data.get("grade")
        != source_data.get("grade")
    ):
        errors.append(
            "GRADE_SOURCE_MISMATCH"
        )

    # --------------------------------------------------------
    # 4. Lesson identity uniqueness
    # --------------------------------------------------------

    lesson_ids = [
        lesson.lesson_id
        for lesson in lessons
    ]

    if (
        len(lesson_ids)
        != len(set(lesson_ids))
    ):
        errors.append(
            "DUPLICATE_LESSON_ID"
        )

    # --------------------------------------------------------
    # 5. Sequence uniqueness
    # --------------------------------------------------------

    sequences = [
        lesson.sequence
        for lesson in lessons
    ]

    if (
        len(sequences)
        != len(set(sequences))
    ):
        errors.append(
            "DUPLICATE_LESSON_SEQUENCE"
        )

    # --------------------------------------------------------
    # 6. Dataset identity consistency
    # --------------------------------------------------------

    for lesson in lessons:

        if (
            lesson.textbook_ref
            != lessons_data["textbook_ref"]
        ):
            errors.append(
                f"TEXTBOOK_REF_MISMATCH:"
                f"{lesson.lesson_id}"
            )

        if (
            lesson.subject
            != lessons_data["subject"]
        ):
            errors.append(
                f"SUBJECT_MISMATCH:"
                f"{lesson.lesson_id}"
            )

        if (
            lesson.grade
            != lessons_data["grade"]
        ):
            errors.append(
                f"GRADE_MISMATCH:"
                f"{lesson.lesson_id}"
            )

    # --------------------------------------------------------
    # 7. Provenance must resolve to registered source
    # --------------------------------------------------------

    for lesson in lessons:

        if (
            lesson.provenance.source_document_id
            != source_id
        ):
            errors.append(
                f"UNKNOWN_TEXTBOOK_SOURCE:"
                f"{lesson.lesson_id}"
            )

    # --------------------------------------------------------
    # 8. Verified lesson requires verified copy
    # --------------------------------------------------------

    for lesson in lessons:

        if (
            lesson.status == "VERIFIED"
            and not lesson.provenance.verified_copy_id
        ):
            errors.append(
                f"VERIFIED_WITHOUT_VERIFIED_COPY:"
                f"{lesson.lesson_id}"
            )

    return errors


def is_textbook_dataset_generation_ready(
    lessons_file: str | Path,
    source_file: str | Path,
) -> bool:
    errors = validate_canonical_textbook_dataset(
        lessons_file,
        source_file,
    )

    if errors:
        return False

    source_data = _load_json(
        source_file
    )

    lessons = load_canonical_textbook_lessons(
        lessons_file
    )

    if (
        source_data.get("status")
        != "VERIFIED"
    ):
        return False

    if not lessons:
        return False

    return all(
        lesson.status == "VERIFIED"
        for lesson in lessons
    )
