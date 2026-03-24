from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime


class ChatSessionOut(BaseModel):
    session_id: str
    messages: list[ChatMessage] = []
