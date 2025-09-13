from pydantic import BaseModel, Field
from typing import List

class Message(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str

class ChatRequest(BaseModel):
    session_id: str | None = None
    messages: List[Message]
