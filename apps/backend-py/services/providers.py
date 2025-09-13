import asyncio
import json
import httpx
from uuid import uuid4
from fastapi import HTTPException
from sqlmodel import Session
from models.message import Message
from models.chat_history import ChatHistory
from services.sse import sse_line
from config import PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, OPENROUTER_API_KEY, OPENROUTER_MODEL

# Optional OpenAI
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

def save_history(session: Session, session_id: str, role: str, content: str):
    record = ChatHistory(session_id=session_id, role=role, content=content)
    session.add(record)
    session.commit()

async def stream_mock(messages, session_id: str, session: Session):
    reply = "Hi! This is the mock provider. Switch PROVIDER=openai or PROVIDER=openrouter for real responses."
    for token in reply.split(" "):
        yield sse_line({"content": token + " "})
        await asyncio.sleep(0.03)
    save_history(session, session_id, "assistant", reply)

async def stream_openai(messages, session_id: str, session: Session):
    if not OPENAI_API_KEY or OpenAI is None:
        raise HTTPException(status_code=400, detail="Missing OpenAI setup.")

    client = OpenAI(api_key=OPENAI_API_KEY)
    stream = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[m.model_dump() for m in messages],
        stream=True,
    )

    reply_text = ""
    for event in stream:
        delta = event.choices[0].delta.content or ""
        if delta:
            reply_text += delta
            yield sse_line({"content": delta})
    save_history(session, session_id, "assistant", reply_text)

async def stream_openrouter(messages, session_id: str, session: Session):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=400, detail="Missing OPENROUTER_API_KEY.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "Brainfish Chat (FastAPI)",
    }
    body = {"model": OPENROUTER_MODEL, "messages": [m.model_dump() for m in messages], "stream": True}
    reply_text = ""

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", "https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers, json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj.get("choices", [{}])[0].get("delta", {}).get("content")
                    if delta:
                        reply_text += delta
                        yield sse_line({"content": delta})
                except Exception:
                    continue
    save_history(session, session_id, "assistant", reply_text)
