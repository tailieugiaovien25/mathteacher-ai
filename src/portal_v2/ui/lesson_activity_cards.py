"""Portable teacher reviewed activity cards for a theory lesson draft.

No card is published by this module. A proposal is never substituted for a
teacher approved card when another AI response arrives.
"""

from __future__ import annotations

from uuid import uuid4


CARD_TYPES = ("TASK", "QUICK_CHECK")
CARD_STATES = ("AI_PROPOSED", "TEACHER_APPROVED")
ACTIVITY_TYPES = ("MO_DAU", "HINH_THANH_KIEN_THUC", "LUYEN_TAP", "VAN_DUNG")


def validate_card(card: object, *, allowed_sources: set[str] | None = None,
                  allowed_questions: set[str] | None = None) -> dict:
    if not isinstance(card, dict) or card.get("kind") not in CARD_TYPES or card.get("activity") not in ACTIVITY_TYPES:
        raise ValueError("Loại thẻ hoặc hoạt động không hợp lệ.")
    if card.get("review_status") not in CARD_STATES:
        raise ValueError("Thẻ phải được đề xuất hoặc giáo viên kiểm tra.")
    for field, maximum in (("id", 80), ("title", 180), ("instruction", 3000),
                           ("expected_product", 500), ("teacher_note", 1000)):
        if not isinstance(card.get(field), str) or len(card[field]) > maximum:
            raise ValueError("Trường thẻ không hợp lệ: " + field)
    if not card["id"] or not card["title"].strip() or not card["instruction"].strip():
        raise ValueError("Thẻ cần mã, tiêu đề và nội dung nhiệm vụ.")
    if type(card.get("duration_minutes")) is not int or not 1 <= card["duration_minutes"] <= 45:
        raise ValueError("Thời lượng thẻ phải từ 1 đến 45 phút.")
    refs = card.get("source_refs")
    if not isinstance(refs, list) or not refs or len(refs) > 12 or any(
        not isinstance(ref, str) or not ref or len(ref) > 200 for ref in refs
    ) or len(set(refs)) != len(refs):
        raise ValueError("Thẻ cần nguồn dữ liệu có thể truy vết.")
    if allowed_sources is not None and not set(refs) <= allowed_sources:
        raise ValueError("AI tham chiếu nguồn không có trong dữ liệu đã chọn.")
    question_id = card.get("question_version_id")
    if card["kind"] == "QUICK_CHECK":
        if not isinstance(question_id, str) or not question_id or len(question_id) > 80:
            raise ValueError("Kiểm tra nhanh cần mã phiên bản câu hỏi.")
        if allowed_questions is not None and question_id not in allowed_questions:
            raise ValueError("Câu hỏi chưa được xác nhận thuộc danh sách đã duyệt.")
        if "question:" + question_id not in refs:
            raise ValueError("Thẻ kiểm tra nhanh cần truy vết câu hỏi.")
    elif question_id is not None:
        raise ValueError("Thẻ giao nhiệm vụ không được gắn đáp án câu hỏi.")
    return card


def make_card(*, kind: str, activity: str, title: str, instruction: str,
              expected_product: str, source_refs: list[str], duration_minutes: int = 5,
              question_version_id: str | None = None, teacher_note: str = "",
              review_status: str = "AI_PROPOSED") -> dict:
    card = {"id": str(uuid4()), "kind": kind, "activity": activity,
            "title": title, "instruction": instruction,
            "expected_product": expected_product, "teacher_note": teacher_note,
            "duration_minutes": duration_minutes, "source_refs": list(source_refs),
            "question_version_id": question_version_id, "review_status": review_status}
    return validate_card(card)


def add_approved_card(draft: dict, card: dict) -> None:
    """Teacher approval is the only way a proposal enters a lesson draft."""
    validate_card(card)
    if card["review_status"] != "TEACHER_APPROVED":
        raise ValueError("Giáo viên phải kiểm tra thẻ trước khi thêm vào bài.")
    cards = draft.setdefault("activity_cards", [])
    if any(existing["id"] == card["id"] for existing in cards):
        raise ValueError("Thẻ này đã có trong bài giảng.")
    cards.append(dict(card, source_refs=list(card["source_refs"])))
