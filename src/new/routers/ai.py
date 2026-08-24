"""AI endpoints — provider settings, connection test, model discovery, chat."""
from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from .. import ai_settings
from ..chat_service import ChatService, _ChatConfigError
from ..schemas import (
    AIConnectionTestRequest,
    AIConnectionTestResult,
    AIModelsRequest,
    AIModelsResponse,
    AISettingsResponse,
    AISettingsUpdate,
    ChatRequest,
    ChatResponse,
)

router = APIRouter(prefix="/api/new/ai", tags=["ai"])
_chat_service = ChatService()


@router.get("/settings", summary="获取 AI 配置（不含 API Key）")
def get_settings() -> AISettingsResponse:
    return AISettingsResponse(**ai_settings.safe_response())


@router.put("/settings", summary="保存 AI 配置（api_key 留空则保留原值）")
def put_settings(payload: AISettingsUpdate = Body(...)) -> AISettingsResponse:
    try:
        return AISettingsResponse(**ai_settings.save(payload.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/settings/key", summary="删除已保存的 API Key")
def delete_key():
    return ai_settings.delete_key()


@router.post("/test", summary="测试与模型服务商的连接")
async def test_connection(payload: AIConnectionTestRequest = Body(default=AIConnectionTestRequest())) -> AIConnectionTestResult:
    return AIConnectionTestResult(**await ai_settings.test_connection(payload.model_dump()))


@router.post("/models", summary="发现可用模型（可选）")
async def discover_models(payload: AIModelsRequest = Body(default=AIModelsRequest())) -> AIModelsResponse:
    return AIModelsResponse(**await ai_settings.list_models(payload.model_dump()))


@router.post("/chat", summary="发送对话消息（基于已上传数据的问答）")
async def chat(payload: ChatRequest = Body(...)) -> ChatResponse:
    try:
        return ChatResponse(
            **await _chat_service.chat(
                [m.model_dump() for m in payload.messages],
                conversation_id=payload.conversation_id,
            )
        )
    except _ChatConfigError as exc:
        raise HTTPException(status_code=503, detail={"code": "ai_unconfigured", "message": str(exc)}) from exc