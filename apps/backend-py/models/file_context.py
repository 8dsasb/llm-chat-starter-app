from sqlmodel import SQLModel, Field
from typing import Optional
import datetime

class FileContext(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str
    filename: str
    content: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
