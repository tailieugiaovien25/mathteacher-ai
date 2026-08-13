from collections import defaultdict
from typing import Any


def is_fallback_key(
    lesson_key: str | None,
) -> bool:
    """Nhận diện LessonKey fallback dạng ..._Pxxx."""

    if not lesson_key:
        return False

    parts = lesson_key.rsplit(
        "_P",
        maxsplit=1,
    )

    if len(parts) != 2:
        return False

    suffix = parts[1]

    return (
        len(suffix) == 3
        and suffix.isdigit()
    )


def build_period_mapping(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Gán TIET_TRONG_BAI cho các record đã có LessonKey.

    Mỗi record tối thiểu cần:
    - lesson_key
    - period

    Quy tắc:
    - LessonKey fallback: TIET_TRONG_BAI = 1
    - Bài có nhiều tiết:
      sắp xếp theo tiết PPCT và đánh số 1, 2, 3...
    """

    groups: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for record in records:
        lesson_key = record.get(
            "lesson_key"
        )

        if not lesson_key:
            continue

        groups[str(lesson_key)].append(
            record
        )

    result: list[
        dict[str, Any]
    ] = []

    for lesson_key, items in groups.items():

        if is_fallback_key(
            lesson_key
        ):
            for item in items:
                mapped_item = dict(
                    item
                )

                mapped_item[
                    "period_in_lesson"
                ] = 1

                result.append(
                    mapped_item
                )

            continue

        sorted_items = sorted(
            items,
            key=lambda item: (
                _to_period_number(
                    item.get("period")
                )
            ),
        )

        for index, item in enumerate(
            sorted_items,
            start=1,
        ):
            mapped_item = dict(
                item
            )

            mapped_item[
                "period_in_lesson"
            ] = index

            result.append(
                mapped_item
            )

    return result


def _to_period_number(
    value: Any,
) -> int:
    """Chuyển tiết PPCT thành số để sắp xếp."""

    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return 999999