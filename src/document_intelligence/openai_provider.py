from __future__ import annotations

import json
import os
from typing import Any

from document_intelligence.ai_provider import (
    AIDocumentProvider,
    AIFieldCandidate,
)
from document_intelligence.contracts import (
    DocumentField,
)


_FIELD_BY_VALUE = {
    field.value: field
    for field in DocumentField
}


class OpenAIDocumentProvider:
    """
    OpenAI-backed implementation of AIDocumentProvider.

    The provider performs extraction only.
    It never modifies a source document.
    """

    DEFAULT_MODEL = "gpt-5.4"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        self._model = (
            model
            or os.getenv("OPENAI_DOCUMENT_MODEL")
            or self.DEFAULT_MODEL
        )

        if client is not None:
            self._client = client
            return

        resolved_api_key = (
            api_key
            or os.getenv("OPENAI_API_KEY")
        )

        if not resolved_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured"
            )

        from openai import OpenAI

        self._client = OpenAI(
            api_key=resolved_api_key
        )

    def analyze(
        self,
        *,
        document_text: str,
    ) -> tuple[AIFieldCandidate, ...]:
        if not document_text.strip():
            return ()

        response = self._client.responses.create(
            model=self._model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You extract lesson-plan metadata. "
                        "Do not guess. "
                        "Return only fields supported by "
                        "explicit evidence in the document."
                    ),
                },
                {
                    "role": "user",
                    "content": document_text,
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "lesson_plan_metadata",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "candidates": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "field": {
                                            "type": "string",
                                            "enum": [
                                                field.value
                                                for field
                                                in DocumentField
                                            ],
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
                    },
                },
            },
        )

        output_text = getattr(
            response,
            "output_text",
            "",
        )

        if not output_text:
            return ()

        payload = json.loads(
            output_text
        )

        candidates = []

        for item in payload.get(
            "candidates",
            [],
        ):
            field = _FIELD_BY_VALUE.get(
                item.get("field")
            )

            if field is None:
                continue

            candidates.append(
                AIFieldCandidate(
                    field=field,
                    value=str(
                        item.get("value", "")
                    ),
                    confidence=float(
                        item.get(
                            "confidence",
                            0.0,
                        )
                    ),
                    evidence=str(
                        item.get(
                            "evidence",
                            "",
                        )
                    ),
                )
            )

        return tuple(candidates)


def is_openai_document_provider(
    provider: object,
) -> bool:
    return isinstance(
        provider,
        AIDocumentProvider,
    )
