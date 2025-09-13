from fastapi import APIRouter
from db import get_session
from models.chat_history import ChatHistory
from sqlmodel import select

router = APIRouter()

@router.get("/history/{session_id}")
def get_history(session_id: str):
    with get_session() as session:
        stmt = select(ChatHistory).where(ChatHistory.session_id == session_id)
        rows = session.exec(stmt).all()
        return [{"role": r.role, "content": r.content} for r in rows]
