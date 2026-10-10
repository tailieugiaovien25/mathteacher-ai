from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from ai_platform.contracts import AIRequest, AIResponse


class OllamaProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class OllamaProvider:
    """Local Ollama provider; no API key and no cloud persistence required."""

    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen3:8b"
    timeout_seconds: float = 120.0
    provider_id: str = "ollama"

    def health(self) -> bool:
        req = request.Request(
            f"{self.base_url}/api/tags",
            headers={"Accept": "application/json"},
            method="GET",
        )
        try:
            with request.urlopen(req, timeout=min(self.timeout_seconds, 5.0)) as response:
                return 200 <= int(response.status) < 300
        except (error.HTTPError, error.URLError, TimeoutError):
            return False

    def list_models(self) -> tuple[str, ...]:
        req = request.Request(
            f"{self.base_url}/api/tags",
            headers={"Accept": "application/json"},
            method="GET",
        )
        try:
            with request.urlopen(req, timeout=min(self.timeout_seconds, 5.0)) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OllamaProviderError("KhÃ´ng Ä‘á»c Ä‘Æ°á»£c danh sÃ¡ch model Ollama.") from exc
        models = raw.get("models") or []
        return tuple(
            str(item.get("name") or "").strip()
            for item in models
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        )

    def stream(self, request_data: AIRequest):
        payload = {
            "model": self.model,
            "stream": True,
            "messages": [
                *([{"role": "system", "content": request_data.system_prompt}] if request_data.system_prompt.strip() else []),
                {"role": "user", "content": request_data.prompt},
            ],
        }
        req = request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            response = request.urlopen(req, timeout=self.timeout_seconds)
        except error.HTTPError as exc:
            raise OllamaProviderError(f"Ollama HTTP error {exc.code}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise OllamaProviderError("Không kết nối được Ollama local.") from exc

        try:
            while True:
                line = response.readline()
                if not line:
                    break
                try:
                    item = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                content = str(((item.get("message") or {}).get("content") or ""))
                if content:
                    yield content
                if item.get("done") is True:
                    break
        finally:
            response.close()
    def generate(self, request_data: AIRequest) -> AIResponse:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                *([{"role": "system", "content": request_data.system_prompt}] if request_data.system_prompt.strip() else []),
                {"role": "user", "content": request_data.prompt},
            ],
        }
        req = request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise OllamaProviderError(f"Ollama HTTP error {exc.code}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise OllamaProviderError("KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c Ollama local.") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OllamaProviderError("Ollama tráº£ vá» dá»¯ liá»‡u khÃ´ng há»£p lá»‡.") from exc
        text = str(((raw.get("message") or {}).get("content") or "")).strip()
        if not text:
            raise OllamaProviderError("Ollama khÃ´ng tráº£ vá» ná»™i dung.")
        return AIResponse(text=text, provider=self.provider_id, model=self.model)
