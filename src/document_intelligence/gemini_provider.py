from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import os
from typing import Any
from urllib import error, request

from document_intelligence.ai_provider import (
    AIDocumentProvider,
    AIFieldCandidate,
)
from document_intelligence.contracts import (
    DocumentField,
)


Transport = Callable[
    [
        str,
        Mapping[str, str],
        Mapping[str, Any],
        float,
    ],
    Mapping[str, Any],
]


_FIELD_BY_VALUE = {
    field.value: field
    for field in DocumentField
}


class GeminiDocumentProviderError(
    RuntimeError
):
    pass


class GeminiDocumentProvider:
    """Gemini implementation of canonical AIDocumentProvider.

    The provider extracts structured metadata only.
    It never modifies the source document.
    """

    DEFAULT_MODEL = "gemini-3.5-flash-lite"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        transport: Transport | None = None,
    ) -> None:
        resolved_api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
        )

        if not resolved_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured"
            )

        if timeout <= 0:
            raise ValueError(
                "timeout must be positive"
            )

        self._api_key = resolved_api_key

        self._model = (
            model
            or os.getenv("GEMINI_DOCUMENT_MODEL")
            or os.getenv("GEMINI_MODEL")
            or self.DEFAULT_MODEL
        )

        self._timeout = timeout

        self._transport = (
            transport
            or self._default_transport
        )

    @property
    def model(
        self,
    ) -> str:
        return self._model

    def analyze(
        self,
        *,
        document_text: str,
    ) -> tuple[AIFieldCandidate, ...]:
        if not document_text.strip():
            return ()

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/"
            f"{self._model}:generateContent"
        )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
        }

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": self._build_prompt(
                                document_text=document_text
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            },
        }

        try:
            response = self._transport(
                url,
                headers,
                payload,
                self._timeout,
            )

        except GeminiDocumentProviderError:
            raise

        except Exception as exc:
            raise GeminiDocumentProviderError(
                "Gemini transport failed"
            ) from exc

        return self._parse_response(
            response
        )

    @staticmethod
    def _build_prompt(
        *,
        document_text: str,
    ) -> str:
        fields = [
            field.value
            for field in DocumentField
        ]

        schema = {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {
                                "type": "string",
                                "enum": fields,
                            },
                            "value": {
                                "type": "string",
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "evidence": {
                                "type": "string",
                            },
                        },
                        "required": [
                            "field",
                            "value",
                            "confidence",
                            "evidence",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": [
                "candidates",
            ],
            "additionalProperties": False,
        }

        return (
            "Bạn là bộ phân tích metadata giáo án.\n"
            "Chỉ trích xuất thông tin có bằng chứng rõ ràng "
            "trong tài liệu.\n"
            "Không đoán, không thêm dữ liệu, không sửa tài liệu nguồn.\n"
            "Trả về duy nhất JSON hợp lệ theo schema sau.\n\n"
            "JSON_SCHEMA:\n"
            f"{json.dumps(schema, ensure_ascii=False)}\n\n"
            "DOCUMENT:\n"
            f"{document_text}"
        )

    @staticmethod
    def _parse_response(
        response: Mapping[str, Any],
    ) -> tuple[AIFieldCandidate, ...]:
        try:
            text = (
                response["candidates"][0]
                ["content"]["parts"][0]["text"]
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            raise GeminiDocumentProviderError(
                "Gemini response does not contain text"
            ) from exc

        if not isinstance(
            text,
            str,
        ):
            raise GeminiDocumentProviderError(
                "Gemini response text is invalid"
            )

        cleaned = text.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            cleaned = "\n".join(
                lines
            ).strip()

        try:
            parsed = json.loads(
                cleaned
            )

        except json.JSONDecodeError as exc:
            raise GeminiDocumentProviderError(
                "Gemini returned invalid JSON"
            ) from exc

        if not isinstance(
            parsed,
            Mapping,
        ):
            raise GeminiDocumentProviderError(
                "Gemini JSON payload must be an object"
            )

        raw_candidates = parsed.get(
            "candidates",
            [],
        )

        if not isinstance(
            raw_candidates,
            list,
        ):
            return ()

        candidates = []

        for item in raw_candidates:
            if not isinstance(
                item,
                Mapping,
            ):
                continue

            field = _FIELD_BY_VALUE.get(
                item.get("field")
            )

            if field is None:
                continue

            value = str(
                item.get(
                    "value",
                    "",
                )
            ).strip()

            if not value:
                continue

            try:
                confidence = float(
                    item.get(
                        "confidence",
                        0.0,
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

            if not (
                0.0
                <= confidence
                <= 1.0
            ):
                continue

            candidates.append(
                AIFieldCandidate(
                    field=field,
                    value=value,
                    confidence=confidence,
                    evidence=str(
                        item.get(
                            "evidence",
                            "",
                        )
                    ),
                )
            )

        return tuple(
            candidates
        )

    @staticmethod
    def _default_transport(
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any],
        timeout: float,
    ) -> Mapping[str, Any]:
        encoded = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

        req = request.Request(
            url,
            data=encoded,
            headers=dict(
                headers
            ),
            method="POST",
        )

        try:
            with request.urlopen(
                req,
                timeout=timeout,
            ) as response:
                raw = response.read()

        except error.HTTPError as exc:
            if exc.code in {
                401,
                403,
            }:
                message = (
                    "Gemini authentication failed"
                )

            elif exc.code == 429:
                message = (
                    "Gemini rate limit exceeded"
                )

            elif exc.code >= 500:
                message = (
                    "Gemini service unavailable"
                )

            else:
                message = (
                    f"Gemini HTTP error: {exc.code}"
                )

            raise GeminiDocumentProviderError(
                message
            ) from exc

        except (
            error.URLError,
            TimeoutError,
        ) as exc:
            raise GeminiDocumentProviderError(
                "Gemini network request failed"
            ) from exc

        try:
            parsed = json.loads(
                raw.decode(
                    "utf-8"
                )
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise GeminiDocumentProviderError(
                "Gemini returned invalid response JSON"
            ) from exc

        if not isinstance(
            parsed,
            Mapping,
        ):
            raise GeminiDocumentProviderError(
                "Gemini response must be an object"
            )

        return parsed
