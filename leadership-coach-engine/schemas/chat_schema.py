from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field

class MessageRequest(BaseModel):
    user_message: str
    session_identifier: str  # Changed from UUID to str for flexibility

class Reference(BaseModel):
    type: str  # "video" or "web"
    source: str
    title: Optional[str] = None

class MessageResult(BaseModel):
    bot_message: str
    message_id: str  # Changed from UUID to str to allow string UUIDs
    references: List[Reference] = []
