import httpx
from typing import Sequence, Any
from loguru import logger
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.base.llms.types import ChatMessage, ChatResponse

from config import config

class VLLMClient(OpenAILike):  # pylint: disable=too-many-ancestors
    """Client for interacting with vLLM server that exposes an OpenAI-compatible API"""
    
    def __init__(self):
        super().__init__(
            model='',  # Will be set during initialization
            api_base=f'{config.llm.BaseUrl}/v1',
            api_key=config.llm.ApiKey,
            max_tokens=config.llm.MaxTokens
        )
        self._model_id = None

    async def initialize(self) -> None:
        """Initialize vLLM client by fetching available model ID from the server"""
        self._model_id = await self._fetch_model_id()
        self.model = self._model_id
        logger.info('Initialized vLLM client with model %s', self._model_id)

    async def _fetch_model_id(self) -> str:
        """Fetch available model ID from vLLM server"""
        try:
            headers = {'Authorization': f'Bearer {config.llm.ApiKey}'}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{config.llm.BaseUrl}/v1/models',
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()

            if not data.get('data'):
                raise ValueError('No models available on vLLM server')

            return data['data'][0]['id']
        except Exception as e:
            raise ValueError(
                f'Failed to fetch model ID from vLLM server: {str(e)}'
            ) from e
    
    async def achat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Override achat to include default stop tokens for better response handling"""
        # Add stop tokens if not provided
        if "stop" not in kwargs:
            kwargs["stop"] = ["user:", "assistant:", "\nuser", "\nassistant"]
        
        # Call the parent class implementation
        return await super().achat(messages, **kwargs)
    
    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Override chat to include default stop tokens for better response handling"""
        # Add stop tokens if not provided
        if "stop" not in kwargs:
            kwargs["stop"] = ["user:", "assistant:", "\nuser", "\nassistant"]
        
        # Call the parent class implementation
        return super().chat(messages, **kwargs)
