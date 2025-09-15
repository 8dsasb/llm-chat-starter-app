from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from uuid import uuid4

from db import get_session
from models.message import ChatRequest
from services import providers
from services.providers import get_file_context
from config import OPENROUTER_MODEL   # for logging OpenRouter model

router = APIRouter()

# ✅ One-time startup log
print(f"[Chat Router] Active provider: {providers.PROVIDER}")
if providers.PROVIDER == "openrouter":
    print(f"[Chat Router] OpenRouter model: {OPENROUTER_MODEL}")

@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    session_id = req.session_id or str(uuid4())

    with get_session() as session:
        # Save user messages
        for m in req.messages:
            providers.save_history(session, session_id, m.role, m.content)

        # Inject file context if available
        file_context = get_file_context(session_id)
        if file_context:
            req.messages.insert(
                0,
                {
                    "role": "system",
                    "content": f"The user has uploaded the following files. Use them when relevant:\n\n{file_context}",
                },
            )

        # Route to selected provider
        if providers.PROVIDER == "mock":
            generator = providers.stream_mock(req.messages, session_id, session)
        elif providers.PROVIDER == "openai":
            generator = providers.stream_openai(req.messages, session_id, session)
        elif providers.PROVIDER == "openrouter":
            # Log each time too
            print(f"[OpenRouter] Using model: {OPENROUTER_MODEL}")
            generator = providers.stream_openrouter(req.messages, session_id, session)
        elif providers.PROVIDER == "hf":
            generator = providers.stream_hf_provider(req.messages, session_id, session)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown PROVIDER: {providers.PROVIDER}")

        async def event_gen():
            async for chunk in generator:
                if await request.is_disconnected():
                    break
                yield chunk

        return StreamingResponse(event_gen(), media_type="text/event-stream")
