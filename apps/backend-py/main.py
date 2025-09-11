import os
import asyncio
import json
from typing import List, Dict, AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlmodel import SQLModel, Field as SQLField, Session, create_engine, select
from uuid import uuid4
import httpx

# Load env vars
load_dotenv()
PROVIDER = os.getenv("PROVIDER", "mock").lower()
DB_URL = os.getenv("DB_URL", "sqlite:///./chat_history.db")

# Database setup
engine = create_engine(DB_URL, echo=False)

class Message(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str

class ChatRequest(BaseModel):
    session_id: str | None = None
    messages: List[Message]

class ChatHistory(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    session_id: str
    role: str
    content: str

SQLModel.metadata.create_all(engine)

# Optional deps
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

app = FastAPI(title="Brainfish Chat (FastAPI)")

# Dev CORS (frontend vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def save_history(session_id: str, role: str, content: str):
    with Session(engine) as session:
        record = ChatHistory(session_id=session_id, role=role, content=content)
        session.add(record)
        session.commit()

def load_history(session_id: str) -> List[Dict]:
    with Session(engine) as session:
        stmt = select(ChatHistory).where(ChatHistory.session_id == session_id)
        rows = session.exec(stmt).all()
        return [{"role": r.role, "content": r.content} for r in rows]

@app.get("/health")
def health():
    return {"ok": True, "provider": PROVIDER}

def sse_line(payload: Dict) -> bytes:
    return f"data: {json.dumps(payload)}\n\n".encode("utf-8")

async def stream_mock(messages: List[Message], session_id: str) -> AsyncGenerator[bytes, None]:
    reply = "Hi! This is the mock provider. Switch PROVIDER=openai or PROVIDER=openrouter for real responses."
    for token in reply.split(" "):
        yield sse_line({"content": token + " "})
        await asyncio.sleep(0.03)
    save_history(session_id, "assistant", reply)

async def stream_openai(messages: List[Message], session_id: str) -> AsyncGenerator[bytes, None]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        raise HTTPException(status_code=400, detail="Missing or invalid OpenAI setup.")
    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    stream = client.chat.completions.create(
        model=model,
        messages=[m.model_dump() for m in messages],
        stream=True,
    )
    reply_text = ""
    for event in stream:
        delta = event.choices[0].delta.content or ""
        if delta:
            reply_text += delta
            yield sse_line({"content": delta})
    save_history(session_id, "assistant", reply_text)

async def stream_openrouter(messages: List[Message], session_id: str) -> AsyncGenerator[bytes, None]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing OPENROUTER_API_KEY.")
    model = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "Brainfish Chat (FastAPI)",
    }
    body = {"model": model, "messages": [m.model_dump() for m in messages], "stream": True}
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
    save_history(session_id, "assistant", reply_text)

@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    session_id = req.session_id or str(uuid4())

    # Save user messages to history
    for m in req.messages:
        save_history(session_id, m.role, m.content)

    history = load_history(session_id)

    if PROVIDER == "mock":
        generator = stream_mock(req.messages, session_id)
    elif PROVIDER == "openai":
        generator = stream_openai(req.messages, session_id)
    elif PROVIDER == "openrouter":
        generator = stream_openrouter(req.messages, session_id)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown PROVIDER: {PROVIDER}")

    async def event_gen():
        async for chunk in generator:
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.get("/api/history/{session_id}")
def get_history(session_id: str):
    return load_history(session_id)
