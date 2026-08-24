"""Workbench chat — OpenAI-compatible conversation grounded in uploaded data.

The model can call the grounding tools in :mod:`ai_tools` to pull real numbers
from the user's data. The loop is deliberately simple:

    user messages -> provider -> tool calls -> execute -> provider -> answer

Final answer is the model's natural-language text. No structured JSON-schema
response is forced (keep it simple).
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Optional

from app.ai.errors import AIAnalystError, AIProviderError
from app.ai.provider import ModelProvider, ToolCall
from . import ai_settings, ai_tools
from . import db as workbench_db

logger = logging.getLogger("workbench.ai.chat")

SYSTEM_PROMPT = """\
你是数据工作台的 AI 助手，帮助用户分析他们上传的木材回收数据。

规则：
1. 回答必须基于工具返回的真实数据。没有工具数据支撑的数字不要编造。
2. 需要数据时调用工具（get_dashboard_summary / get_monthly_trend / \
get_route_distribution / get_source_distribution / get_species_distribution / \
list_batches / get_batch_detail）。
3. 用简洁的中文回答，给出结论并引用关键数字和单位。
4. 如果数据不足，明确说明缺少哪些数据。
5. 不要编造不存在的批次、物料或成本。"""


class ChatService:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def chat(
        self,
        messages: list[dict[str, str]],
        conversation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        cid = conversation_id or f"conv_{uuid.uuid4().hex}"
        try:
            provider = ai_settings.build_provider()
        except ValueError as exc:
            raise _ChatConfigError(str(exc)) from exc

        effective = ai_settings.effective()
        history = [{"role": m["role"], "content": m["content"]} for m in messages if m.get("content")]
        if not history or history[-1]["role"] != "user":
            raise _ChatConfigError("消息格式不正确：最后一条必须是用户消息。")

        system = SYSTEM_PROMPT
        tools = ai_tools.provider_tools()
        tools_used: list[str] = []

        async with self._lock:
            conn = workbench_db.connect()
            try:
                try:
                    reply, tools_used = await self._run(provider, system, history, tools, conn)
                except AIAnalystError as exc:
                    raise _ChatConfigError(str(exc)) from exc
            finally:
                conn.close()

        return {
            "reply": reply,
            "conversation_id": cid,
            "tools_used": sorted(set(tools_used)),
            "model": provider.model,
            "provider": effective["provider"],
        }

    async def _run(
        self,
        provider: ModelProvider,
        system: str,
        history: list[dict[str, str]],
        tools: list[dict[str, Any]],
        conn,
    ) -> tuple[str, list[str]]:
        messages: list[dict[str, Any]] = list(history)
        tools_used: list[str] = []
        rounds = 0

        while True:
            turn = await provider.chat(
                system=system,
                messages=messages,
                tools=tools,
                response_format=None,
                temperature=0.2,
            )
            if not turn.tool_calls:
                return (turn.content or "").strip() or "（模型没有返回内容。）", tools_used
            if rounds >= 6:
                raise AIProviderError("模型工具调用轮次超过安全上限。")

            messages.append(_assistant_tool_message(turn.content, turn.tool_calls))
            for tc in turn.tool_calls:
                tools_used.append(tc.name)
                result = await asyncio.to_thread(self._execute_tool, conn, tc)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )
            rounds += 1

    @staticmethod
    def _execute_tool(conn, tc: ToolCall) -> dict[str, Any]:
        tool = ai_tools.TOOL_BY_NAME.get(tc.name)
        if tool is None:
            return {"success": False, "error": f"未知工具 {tc.name}"}
        args = tc.arguments if isinstance(tc.arguments, dict) else {}
        return tool.run(conn, args)


def _assistant_tool_message(content: Optional[str], tool_calls: list[ToolCall]) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False, default=str)},
            }
            for tc in tool_calls
        ],
    }


class _ChatConfigError(Exception):
    pass