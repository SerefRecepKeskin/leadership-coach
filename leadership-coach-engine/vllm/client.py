import httpx
from llama_index.llms.openai_like import OpenAILike

from prompt import CONVERSATIONAL_SYSTEM_PROMPT
from loguru import logger
from config import config

class VLLMClient(OpenAILike):  # pylint: disable=too-many-ancestors
    def __init__(self):
        super().__init__(
            model='',  # Will be set during initialization
            api_base=f'{config.llm.BaseUrl}/v1',
            api_key=config.llm.ApiKey,
            system_prompt=CONVERSATIONAL_SYSTEM_PROMPT,
            max_tokens=config.llm.MaxTokens
        )

        self._model_id = None

    async def initialize(self) -> None:
        """
        Initialize vLLM client
        """
        self._model_id = await self._fetch_model_id()
        self.model = self._model_id
        logger.info('Initialized with model %s', self._model_id)

    async def _fetch_model_id(self) -> str:
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
