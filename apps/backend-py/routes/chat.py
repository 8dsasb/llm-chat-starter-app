from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from uuid import uuid4

from db import get_session
from models.message import ChatRequest
from models.chat_history import ChatHistory
from services import providers

router = APIRouter()

@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    session_id = req.session_id or str(uuid4())

    with get_session() as session:
        # Save user messages
        for m in req.messages:
            providers.save_history(session, session_id, m.role, m.content)

        # Route provider
        if providers.PROVIDER == "mock":
            generator = providers.stream_mock(req.messages, session_id, session)
        elif providers.PROVIDER == "openai":
            generator = providers.stream_openai(req.messages, session_id, session)
        elif providers.PROVIDER == "openrouter":
            generator = providers.stream_openrouter(req.messages, session_id, session)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown PROVIDER: {providers.PROVIDER}")

        async def event_gen():
            async for chunk in generator:
                if await request.is_disconnected():
                    break
                yield chunk

        return StreamingResponse(event_gen(), media_type="text/event-stream")
