from sqlmodel import SQLModel, create_engine, Session
from config import DB_URL

# Import models so SQLModel is aware of them
from models.chat_history import ChatHistory
from models.file_context import FileContext   # ✅ add this

engine = create_engine(DB_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
