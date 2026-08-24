"""Gemini-backed lesson-plan revision service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class GeminiLessonPlanError(RuntimeError):
    """User-safe error raised when Gemini cannot revise a document."""


Transport = Callable[[Request, float], Any]


def _default_transport(request: Request, timeout: float):
    return urlopen(request, timeout=timeout)


@dataclass(frozen=True)
class GeminiLessonPlanService:
    api_key: str
    model: str = "gemini-3.5-flash-lite"
    timeout_seconds: float = 90.0
    transport: Transport = _default_transport

    def revise(
        self,
        *,
        request: str,
        document: str,
        context: dict[str, Any],
    ) -> str:
        if not self.api_key.strip():
            raise GeminiLessonPlanError("Chưa cấu hình GEMINI_API_KEY.")
        if not request.strip():
            raise GeminiLessonPlanError("Yêu cầu AI không được để trống.")
        if len(document) > 180_000:
            raise GeminiLessonPlanError(
                "Giáo án quá dài để xử lý trong một lượt. "
                "Hãy chia tài liệu thành các phần nhỏ hơn."
            )

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": self._build_prompt(request, document, context)}],
                }
            ],
            "generationConfig": {
                "temperature": 0.25,
                "maxOutputTokens": 16384,
            },
        }
        api_request = Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        try:
            with self.transport(api_request, self.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = self._http_error_message(error)
            raise GeminiLessonPlanError(detail) from error
        except URLError as error:
            raise GeminiLessonPlanError(
                "Không thể kết nối Gemini. Hãy kiểm tra Internet rồi thử lại."
            ) from error
        except TimeoutError as error:
            raise GeminiLessonPlanError(
                "Gemini phản hồi quá thời gian cho phép. Hãy thử lại."
            ) from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GeminiLessonPlanError(
                "Gemini trả về dữ liệu không hợp lệ. Hãy thử lại."
            ) from error

        text = self._extract_text(result)
        if not text:
            raise GeminiLessonPlanError(
                "Gemini chưa tạo được nội dung. Hãy điều chỉnh yêu cầu rồi thử lại."
            )
        return text

    @staticmethod
    def _build_prompt(
        request: str,
        document: str,
        context: dict[str, Any],
    ) -> str:
        fields = (
            ("Môn/phân môn", context.get("subject_name")),
            ("Lớp", context.get("class_name")),
            ("Tên bài dạy", context.get("lesson_title")),
            ("Tiết PPCT", context.get("curriculum_period")),
            ("Tiết TKB", context.get("timetable_period")),
            ("Ngày thực hiện", context.get("teaching_date")),
        )
        context_text = "\n".join(
            f"- {label}: {value if value not in (None, '') else '-'}"
            for label, value in fields
        )
        return f"""Bạn là trợ lý chuyên môn dành cho giáo viên Việt Nam.
Hãy chỉnh sửa Kế hoạch bài dạy theo đúng yêu cầu của giáo viên.

NGUYÊN TẮC BẮT BUỘC:
- Trả về toàn bộ giáo án sau khi chỉnh sửa, không chỉ phần thay đổi.
- Giữ nguyên dữ kiện đúng, cấu trúc cần thiết và tiếng Việt có dấu.
- Không tự ý thay đổi môn, lớp, tên bài, tiết PPCT, tiết TKB hoặc ngày thực hiện.
- Không thêm lời chào, lời giải thích hay hàng rào Markdown.
- Không tạo thông tin cá nhân của học sinh.

THÔNG TIN TỪ LỊCH BÁO GIẢNG:
{context_text}

YÊU CẦU CỦA GIÁO VIÊN:
{request.strip()}

GIÁO ÁN HIỆN TẠI:
{document.strip() or '[Chưa có nội dung. Hãy tạo bản giáo án phù hợp.]'}
"""

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        candidates = payload.get("candidates") or []
        if not candidates:
            return ""
        parts = (candidates[0].get("content") or {}).get("parts") or []
        return "\n".join(
            str(part.get("text", ""))
            for part in parts
            if str(part.get("text", "")).strip()
        ).strip()

    @staticmethod
    def _http_error_message(error: HTTPError) -> str:
        status = int(getattr(error, "code", 0) or 0)
        if status in (401, 403):
            return "Gemini API key không hợp lệ hoặc chưa được cấp quyền."
        if status == 429:
            return (
                "Gemini Free Tier đang hết hạn mức tạm thời. "
                "Hãy chờ một lúc rồi thử lại."
            )
        if status >= 500:
            return "Dịch vụ Gemini đang gián đoạn. Hãy thử lại sau."
        return f"Gemini không xử lý được yêu cầu (mã lỗi {status or 'không xác định'})."
