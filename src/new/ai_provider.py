"""Model provider abstraction.

`ModelProvider` is the boundary the rest of the system depends on. Only ONE concrete
provider is wired at runtime via configuration (OpenAI-compatible HTTP). All
provider-specific concerns (auth, URL, error mapping) live inside the adapter — never in
business or orchestration logic.

`FakeModelProvider` is a scripted stand-in used by offline tests; it implements the same
interface so orchestration can be exercised without any paid/live model.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol, runtime_checkable

import httpx

from .config import AI_REQUEST_TIMEOUT
from .ai_errors import (
    AIProviderAuth,
    AIProviderMalformedResponse,
    AIProviderRateLimit,
    AIProviderTimeout,
    AIProviderUnavailable,
)


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ModelTurn:
    content: Optional[str]
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Optional[dict[str, Any]] = None


@runtime_checkable
class ModelProvider(Protocol):
    async def chat(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        response_format: Optional[dict[str, Any]],
        temperature: float,
    ) -> ModelTurn:
        ...


def _map_http_error(exc: httpx.HTTPStatusError) -> Exception:
    status = exc.response.status_code
    if status in (401, 403):
        return AIProviderAuth("Model provider rejected the credentials.")
    if status == 429:
        return AIProviderRateLimit("Model provider rate limit reached.")
    if status >= 500:
        return AIProviderUnavailable("Model provider is temporarily unavailable.")
    return AIProviderMalformedResponse(f"Model provider returned HTTP {status}.")


class OpenAICompatibleProvider:
    """Provider for any OpenAI-compatible chat-completions endpoint.

    Works with OpenAI, OpenRouter, Azure OpenAI, and most local OpenAI-compatible
    servers. API key and base URL come exclusively from configuration.
    """

    def __init__(self, *, model: str, api_key: str, base_url: str, timeout: float = AI_REQUEST_TIMEOUT) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def chat(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        response_format: Optional[dict[str, Any]],
        temperature: float,
    ) -> ModelTurn:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": temperature,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        if response_format is not None:
            body["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions", json=body, headers=headers
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise AIProviderTimeout("Model provider request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise _map_http_error(exc) from exc
        except httpx.ConnectError as exc:
            raise AIProviderUnavailable("Could not reach the model provider.") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise AIProviderMalformedResponse("Model provider returned an invalid response.") from exc

        return self._parse(data)

    @staticmethod
    def _parse(data: dict[str, Any]) -> ModelTurn:
        try:
            msg = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderMalformedResponse("Model provider response missing 'choices'.") from exc

        content = msg.get("content")
        tool_calls: list[ToolCall] = []
        for tc in msg.get("tool_calls") or []:
            if tc.get("type") != "function":
                continue
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(id=tc.get("id", "call_0"), name=fn.get("name", ""), arguments=args))
        return ModelTurn(content=content, tool_calls=tool_calls, raw=data)


@dataclass
class ScriptedTurn:
    tool_calls: list[ToolCall] = field(default_factory=list)
    content: Optional[str] = None


class FakeModelProvider:
    """Scripted provider for offline tests. Returns pre-arranged turns in order.

    Each `chat()` call consumes the next scripted turn. The final turn (synthesis) should
    carry `content` (JSON). The provider also records every call so tests can assert on
    conversation continuity.
    """

    def __init__(
        self,
        script: list[ScriptedTurn],
        on_call: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self._script = list(script)
        self._idx = 0
        self.on_call = on_call
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        response_format: Optional[dict[str, Any]],
        temperature: float,
    ) -> ModelTurn:
        record = {
            "system": system,
            "messages": messages,
            "tools_present": bool(tools),
            "response_format_present": response_format is not None,
        }
        self.calls.append(record)
        if self.on_call is not None:
            self.on_call(record)

        if self._idx >= len(self._script):
            # Out of script — behave like a model that stops calling tools.
            return ModelTurn(content="{}", tool_calls=[])
        turn = self._script[self._idx]
        self._idx += 1
        return ModelTurn(content=turn.content, tool_calls=list(turn.tool_calls))


def build_provider(model: str, api_key: str, base_url: str, timeout: float = AI_REQUEST_TIMEOUT) -> ModelProvider:
    """Factory returning the configured concrete provider (OpenAI-compatible)."""
    return OpenAICompatibleProvider(model=model, api_key=api_key, base_url=base_url, timeout=timeout)
