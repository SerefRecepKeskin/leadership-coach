from typing import AnyStr, Dict

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.memory import ChatMemoryBuffer

from . import get_store


class SessionManager:
    def __init__(self):
        self._chat_store = get_store()

        self._active_sessions: Dict[AnyStr: ChatMemoryBuffer] = {}

    async def get_or_create_session(
        self,
        user_id: str,
        session_id: str
    ) -> ChatMemoryBuffer:
        """
        Get or create user session

        :param user_id: user identifier
        :param session_id: session identifier
        :return: chat memory object
        """
        if session_id not in self._active_sessions:
            chat_memory = ChatMemoryBuffer.from_defaults(
                token_limit=2048,
                chat_store=self._chat_store,
                chat_store_key=f'{user_id}:{session_id}'
            )

            self._active_sessions[session_id] = chat_memory

        return self._active_sessions[session_id]

    async def save_messages(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str
    ) -> None:
        """
        Save messages to chat memory

        :param session_id: session identifier
        :param user_message: user message
        :param assistant_message: assistant's message for reply to user message
        :return: chat memory object
        """
        messages = []

        messages.append(ChatMessage(
            role=MessageRole.USER,
            content=user_message
        ))

        messages.append(ChatMessage(
            role=MessageRole.ASSISTANT,
            content=assistant_message
        ))

        await self._active_sessions[session_id].aput_messages(messages)

    async def close_session(self, session_id: str) -> None:
        """
        Close user session and reset memory

        :param session_id: session identifier
        """
        chat_memory = self._active_sessions.pop(session_id)

        chat_memory.reset()
