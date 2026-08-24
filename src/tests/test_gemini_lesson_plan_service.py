import json

from portal_v2.ai.gemini_lesson_plan_service import GeminiLessonPlanService


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_service_sends_schedule_context_and_returns_full_text():
    captured = {}

    def transport(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(
            {"candidates": [{"content": {"parts": [{"text": "GIÁO ÁN MỚI"}]}}]}
        )

    service = GeminiLessonPlanService(api_key="secret", transport=transport)
    result = service.revise(
        request="Bổ sung hoạt động mở đầu",
        document="GIÁO ÁN CŨ",
        context={
            "subject_name": "Số học",
            "class_name": "6A1",
            "lesson_title": "Thứ tự thực hiện phép tính",
            "curriculum_period": 10,
            "timetable_period": 2,
            "teaching_date": "22/08/2026",
        },
    )

    prompt = captured["body"]["contents"][0]["parts"][0]["text"]
    assert result == "GIÁO ÁN MỚI"
    assert "Số học" in prompt
    assert "6A1" in prompt
    assert "Tiết PPCT: 10" in prompt
    assert "Tiết TKB: 2" in prompt
    assert "GIÁO ÁN CŨ" in prompt
    assert captured["timeout"] == 90.0


def test_default_model_uses_current_free_tier_flash_lite():
    assert GeminiLessonPlanService(api_key="secret").model == "gemini-3.5-flash-lite"
