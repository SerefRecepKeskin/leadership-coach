from uuid import UUID

from pydantic import BaseModel, Field

class MessageRequest(BaseModel):
    user_message: str
    session_identifier: str  # Changed from UUID to str for flexibility

class MessageResult(BaseModel):
    bot_message: str
    message_id: str  # Changed from UUID to str to allow string UUIDs
