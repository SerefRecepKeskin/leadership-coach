"""Module for chat services"""

from typing import Optional
from uuid import uuid4, UUID

from chatbot.worker import ChatbotWorker
from schemas.chat_schema import MessageResult

# Create a single worker instance
chatbot_worker = None

async def initialize_worker():
    """Initialize the chatbot worker"""
    global chatbot_worker
    if chatbot_worker is None:
        chatbot_worker = await ChatbotWorker.create()

async def get_welcome_message() -> MessageResult:
    """
    Creates a static welcome message in Turkish for new chat sessions.

    :return: The Turkish welcome message as a MessageResult object.
    """
    result = {
        "bot_message": """👋 Liderlik Koçu'na Hoş Geldiniz! 👋

        Liderlik becerilerinizi geliştirmenize ve zorluklarla başa çıkmanıza yardımcı olmak için buradayım.
        Bugün size nasıl yardımcı olabilirim?""",
        "message_id": str(uuid4()),
        "references": []  # Add empty references for welcome message
    }
    return MessageResult(**result)


async def create_bot_response(session_identifier: str, user_message: str) -> Optional[MessageResult]:
    """Generates a bot response to a user's message using the chatbot worker.

    :param session_identifier: The unique identifier of the session.
    :param user_message: The user's message to which the bot should respond.
    :return: The bot's response as a `MessageResult` object.
    """
    # Initialize worker if not already initialized
    await initialize_worker()

    # Use worker to process the prompt
    response = await chatbot_worker.process_prompt_async(
        session_id=session_identifier,
        user_message=user_message
    )

    result = {
        "bot_message": response["response"],
        "message_id": str(uuid4()),
        "references": response.get("references", [])  # Include references from worker response
    }

    return MessageResult(**result)
