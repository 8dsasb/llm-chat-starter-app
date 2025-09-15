import asyncio
import json
import os
import httpx
from uuid import uuid4
from fastapi import HTTPException
from sqlmodel import Session, select
from models.message import Message
from models.chat_history import ChatHistory
from services.sse import sse_line
from config import PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, OPENROUTER_API_KEY, OPENROUTER_MODEL
from models.file_context import FileContext
from db import get_session
from config import OPENROUTER_MODEL

# Use new Hugging Face provider
from services.hf_provider import stream_hf

PROVIDER = os.getenv("PROVIDER", "mock")  # default = mock

def stream_hf_provider(messages, session_id, session):
    return stream_hf(messages, session_id, session)


# Optional OpenAI
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def get_file_context(session_id: str) -> str:
    """Collect all file contexts for a session and merge into one string."""
    with get_session() as session:
        files = session.exec(
            select(FileContext).where(FileContext.session_id == session_id)
        ).all()

    if not files:
        return ""

    parts = []
    for f in files:
        parts.append(f"[File: {f.filename}]\n{f.content}")
    return "\n\n".join(parts)


def save_history(session: Session, session_id: str, role: str, content: str):
    record = ChatHistory(session_id=session_id, role=role, content=content)
    session.add(record)
    session.commit()


async def stream_mock(messages, session_id: str, session: Session):
    reply = "Hi! This is the mock provider. Switch PROVIDER=openai, PROVIDER=openrouter, or PROVIDER=hf for real responses."
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
    body = {
        "model": OPENROUTER_MODEL,
        "messages": [
            m.model_dump() if hasattr(m, "model_dump") else m for m in messages
        ],
        "stream": True,
    }

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
