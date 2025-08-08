from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMClient:
    def complete(
        self,
        messages: List[LLMMessage],
        *,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        timeout: float = 30.0,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        raise NotImplementedError


class OpenAICompatClient(LLMClient):
    def __init__(self, base_url: str, api_key: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def complete(
        self,
        messages: List[LLMMessage],
        *,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        timeout: float = 30.0,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Lazy import to avoid hard dependency when AI is disabled
        try:
            import httpx  # type: ignore
        except Exception as e:  # noqa: BLE001
            raise RuntimeError("httpx is required for OpenAI-compatible client") from e

        payload: Dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [m.__dict__ for m in messages],
        }
        if extra:
            payload.update(extra)
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = f"{self.base_url}/v1/chat/completions"
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"unexpected response from LLM: {data}") from e


def create_llm_client(*, endpoint: Optional[str], api_key: Optional[str]) -> Optional[LLMClient]:
    if endpoint:
        return OpenAICompatClient(base_url=endpoint, api_key=api_key)
    return None
