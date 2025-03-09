"""Module for chat related routes"""

from uuid import UUID
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from schemas.chat_schema import MessageRequest
from services.chat_service import (
    create_bot_response,
    get_welcome_message
)

chat_router = APIRouter(
    prefix="/chat"
)

@chat_router.get("/welcome")
async def welcome_message():
    """Returns a static welcome message when user first opens the chat."""
    result = await get_welcome_message()
    return JSONResponse(content=result.dict())

@chat_router.post("/message")
async def message_route(
    message_request: MessageRequest
):
    """Processes the user's message and returns a bot response."""
    result = await create_bot_response(
        session_identifier=message_request.session_identifier,
        user_message=message_request.user_message
    )
    return JSONResponse(content=result.dict())
