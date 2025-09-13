from sqlmodel import SQLModel, Field

class ChatHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: str
    role: str
    content: str
