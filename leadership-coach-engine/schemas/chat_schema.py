from uuid import UUID

from pydantic import BaseModel, Field

class MessageRequest(BaseModel):
    user_message: str
    session_identifier: UUID

class MessageResult(BaseModel):
    bot_message: str
    message_id: UUID
