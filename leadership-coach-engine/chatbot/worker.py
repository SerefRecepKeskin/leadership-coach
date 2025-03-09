from typing import Dict

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore

from config import config
from prompt import CONVERSATIONAL_SYSTEM_PROMPT
from session.manager import SessionManager
from vllm.client import VLLMClient


class ChatbotWorker:
    def __init__(self):
        # chat engine for processing prompts
        self.chat_engine = None

        # create session manager object to manage sessions
        self._session_manager = SessionManager()

    async def _initialize(self) -> None:
        try:
            # initialize the embedding model from Hugging Face
            embed_model = HuggingFaceEmbedding(
                model_name=config.embedding.model,
                cache_folder=config.embedding.cache_dir
            )

            # set up the Milvus vector store
            vector_store = MilvusVectorStore(
                uri=f'http://{config.milvus.url}:{config.milvus.port}',
                collection_name=config.milvus.CollectionName,
                token=config.milvus.Password,
                overwrite=False,
                embedding_field=config.milvus.VectorFieldName,
                output_fields=['video_title', 'video_url', 'transcript_chunk'],
                text_key='transcript_chunk'
            )

            # create and initialize the language model client
            llm = VLLMClient()  # Initialize with no parameters, as the constructor doesn't take any
            await llm.initialize()

            # set global settings for llama_index
            Settings.llm = llm
            Settings.embed_model = embed_model

            # build the vector store index
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=embed_model
            )

            # configure the retriever for top-k similarity search
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=3,
                vector_store_kwargs={
                    'search_params': {'metric_type': 'COSINE'}
                }
            )

            similarity_postprocessor = SimilarityPostprocessor(
                similarity_cutoff=config.milvus.DistanceThreshold
            )

            self.chat_engine = ContextChatEngine.from_defaults(
                retriever=retriever,
                node_postprocessors=[similarity_postprocessor],
                system_prompt=CONVERSATIONAL_SYSTEM_PROMPT
            )
        except Exception as e:
            raise RuntimeError(
                f'Failed to initialize ChatbotWorker: {str(e)}'
            ) from e

    @classmethod
    async def create(cls) -> "ChatbotWorker":
        """
        Create chatbot worker

        :return: ChatbotWorker instance
        """
        # instantiate the class
        instance = cls()

        # perform asynchronous initialization
        await instance._initialize()

        return instance

    async def process_prompt_async(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, str]:
        """
        Process user message to return response from chat engine

        :return: chat engine response
        """
        try:
            # get or create user session to getting memory buffer object
            session = await self._session_manager.get_or_create_session(session_id)

            # get chat history from the user session
            chat_history = session.get()

            # get response by user message and chat history
            query_result = await self.chat_engine.achat(
                user_message,
                chat_history=chat_history
            )

            answer = query_result.response

            # split message to get answer
            answer = answer.split('\nuser')[0]

            await self._session_manager.save_messages(
                session_id=session_id,
                user_message=user_message,
                assistant_message=answer
            )

            return {'response': answer}
        except Exception as e:
            raise RuntimeError(
                f'Error processing message: {str(e)}'
            ) from e
