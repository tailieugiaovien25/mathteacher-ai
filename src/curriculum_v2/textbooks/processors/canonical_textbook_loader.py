import json
from pathlib import Path

from curriculum_v2.textbooks.models import (
    CanonicalTextbookLesson,
    TextbookLessonProvenance,
)


def load_canonical_textbook_lessons(
    file_path: str | Path,
) -> list[CanonicalTextbookLesson]:
    path = Path(file_path)

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        data = json.load(file)

    textbook_ref = data["textbook_ref"]
    subject = data["subject"]
    grade = data["grade"]
    schema_version = data.get(
        "schema_version",
        1,
    )

    lessons = []

    for item in data["lessons"]:
        provenance_data = item["provenance"]

        provenance = TextbookLessonProvenance(
            source_document_id=(
                provenance_data[
                    "source_document_id"
                ]
            ),
            publisher=(
                provenance_data["publisher"]
            ),
            verified_copy_id=(
                provenance_data.get(
                    "verified_copy_id"
                )
            ),
            source_location=(
                provenance_data.get(
                    "source_location"
                )
            ),
            source_version=(
                provenance_data.get(
                    "source_version"
                )
            ),
        )

        lesson = CanonicalTextbookLesson(
            lesson_id=item["lesson_id"],
            textbook_ref=textbook_ref,
            subject=subject,
            grade=grade,
            title=item["title"],
            sequence=item["sequence"],
            provenance=provenance,
            lesson_kind=item.get(
                "lesson_kind",
                "LESSON",
            ),
            unit_ref=item.get(
                "unit_ref"
            ),
            unit_title=item.get(
                "unit_title"
            ),
            status=item.get(
                "status",
                "CANDIDATE",
            ),
            schema_version=schema_version,
        )

        lessons.append(lesson)

    return lessons
