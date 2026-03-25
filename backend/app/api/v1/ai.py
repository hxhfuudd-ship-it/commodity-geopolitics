from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json

from app.schemas.ai import ChatRequest, ChatSessionOut
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI助手"])


@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    session_id = req.session_id or await ai_service.create_session()

    async def event_stream():
        async for chunk in ai_service.chat(
            session_id, req.message, disconnect_check=request.is_disconnected
        ):
            if await request.is_disconnected():
                break
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat/new")
async def new_session():
    session_id = await ai_service.create_session()
    return {"session_id": session_id}


@router.get("/chat/{session_id}/history", response_model=ChatSessionOut)
async def chat_history(session_id: str):
    messages = await ai_service.get_history(session_id)
    return ChatSessionOut(session_id=session_id, messages=messages)
