from __future__ import annotations

import json
from dataclasses import dataclass, field
from urllib import error, request

from ai_platform.contracts import AIRequest, AIResponse


class OllamaProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class OllamaProvider:
    """Ollama local or cloud API provider."""

    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen3:8b"
    timeout_seconds: float = 120.0
    provider_id: str = "ollama"
    api_key: str = field(default="", repr=False, compare=False)

    def _authorization_headers(self) -> dict[str, str]:
        key = self.api_key.strip()
        return {"Authorization": f"Bearer {key}"} if key else {}

    @staticmethod
    def _context_options(request_data: AIRequest) -> dict[str, dict[str, int]]:
        raw_num_ctx = request_data.metadata.get("ollama_num_ctx")
        if raw_num_ctx is None:
            return {}
        try:
            num_ctx = int(raw_num_ctx)
        except (TypeError, ValueError) as exc:
            raise OllamaProviderError("Ollama num_ctx must be an integer.") from exc
        if not 512 <= num_ctx <= 32768:
            raise OllamaProviderError("Ollama num_ctx must be between 512 and 32768.")
        return {"options": {"num_ctx": num_ctx}}

    def health(self) -> bool:
        req = request.Request(
            f"{self.base_url}/api/tags",
            headers={"Accept": "application/json", **self._authorization_headers()},
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
            headers={"Accept": "application/json", **self._authorization_headers()},
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
        payload.update(self._context_options(request_data))
        req = request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                **self._authorization_headers(),
            },
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
        payload.update(self._context_options(request_data))
        req = request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", **self._authorization_headers()},
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
