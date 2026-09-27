"""Conservative checks before an AI authored question is saved for review."""

from __future__ import annotations

from difflib import SequenceMatcher
import re
import unicodedata


def normalized_prompt(value: str) -> str:
    text = unicodedata.normalize("NFC", value).casefold()
    text = re.sub(r"\\(?:left|right|mathrm|text|mathbf)\b", "", text)
    text = text.replace("\\times", "×").replace("\\cdot", "·")
    text = text.replace("\\{", "{").replace("\\}", "}")
    text = re.sub(r"[\u200b-\u200f\ufeff]", "", text)
    return re.sub(r"\s+", " ", text).strip(" .?!")


def resembles(left: str, right: str) -> bool:
    a, b = normalized_prompt(left), normalized_prompt(right)
    if not a or not b:
        return False
    if a == b:
        return True
    # A conservative warning. Numbers and formula tokens remain significant.
    if len(a) < 35 or len(b) < 35:
        return False
    return SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.88


def duplicate_warnings(prompt: str, others: list[str]) -> list[str]:
    return [f"Câu giống câu đã có: {other[:100]}" for other in others
            if resembles(prompt, other)]


def validate_candidate(candidate: object, question_type: str,
                       other_prompts: list[str], target_score: float | None = None) -> list[str]:
    if not isinstance(candidate, dict):
        return ["JSON phải là một đối tượng câu hỏi."]
    issues = []
    for key in ("prompt_text", "solution", "answer"):
        if not isinstance(candidate.get(key), str) or not candidate[key].strip():
            issues.append(f"Thiếu {key}.")
    for key in ("prompt_text", "solution", "answer"):
        text = candidate.get(key, "")
        if isinstance(text, str) and ("�" in text or re.search(r"[\u200b-\u200f\ufeff]", text)
                                      or any(ord(char) < 32 and char not in '\n\t' for char in text)):
            issues.append(f"{key} có ký tự lỗi hoặc ký tự ẩn.")
    if question_type == "MULTIPLE_CHOICE":
        options = candidate.get("options")
        if not isinstance(options, list) or len(options) != 4:
            issues.append("Trắc nghiệm cần đúng 4 phương án.")
        else:
            if any(not isinstance(o, dict) or not isinstance(o.get("text"), str)
                   or not o["text"].strip() or type(o.get("is_correct")) is not bool
                   for o in options):
                issues.append("Mỗi phương án cần nội dung và is_correct dạng true/false.")
            else:
                if sum(o["is_correct"] for o in options) != 1:
                    issues.append("Trắc nghiệm cần đúng một đáp án đúng.")
                else:
                    correct_code = "ABCD"[next(i for i, o in enumerate(options) if o["is_correct"])]
                    answer = str(candidate.get("answer", "")).strip()
                    marked = re.match(r"^([A-D])(?:[.)\s:]|$)", answer, flags=re.IGNORECASE)
                    if marked and marked.group(1).upper() != correct_code:
                        issues.append("Nhãn đáp án không khớp phương án được đánh dấu đúng.")
                if len({normalized_prompt(o["text"]) for o in options}) != 4:
                    issues.append("Các phương án đang trùng nhau.")
    elif question_type == "TRUE_FALSE":
        statements = candidate.get("statements")
        if not isinstance(statements, list) or len(statements) != 4:
            issues.append("Đúng/Sai cần đúng 4 nhận định.")
        elif any(not isinstance(s, dict) or not isinstance(s.get("text"), str)
                 or not s["text"].strip() or type(s.get("correct_value")) is not bool
                 for s in statements):
            issues.append("Mỗi nhận định cần nội dung và correct_value dạng true/false.")
        elif len({normalized_prompt(s["text"]) for s in statements}) != 4:
            issues.append("Các nhận định đang trùng nhau.")
    elif question_type == "ESSAY":
        steps = candidate.get("scoring_steps")
        if not isinstance(steps, list) or not steps:
            issues.append("Tự luận cần các bước chấm điểm.")
        elif any(not isinstance(s, dict) or not isinstance(s.get("description"), str)
                 or not s["description"].strip() or type(s.get("score")) not in (int, float)
                 or s["score"] <= 0 for s in steps):
            issues.append("Mỗi bước chấm cần mô tả và số điểm dương.")
        elif target_score is not None and abs(sum(s["score"] for s in steps) - target_score) > 0.001:
            issues.append("Tổng điểm các bước chấm không bằng điểm câu hỏi.")
    elif question_type != "SHORT_RESPONSE" and question_type != "MULTIPLE_CHOICE":
        issues.append("Dạng câu hỏi chưa được hỗ trợ.")
    prompt = candidate.get("prompt_text")
    if isinstance(prompt, str):
        issues.extend(duplicate_warnings(prompt, other_prompts))
    return issues
