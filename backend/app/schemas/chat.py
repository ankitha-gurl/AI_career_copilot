from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatMessageOut(BaseModel):
    role: str
    content: str


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
