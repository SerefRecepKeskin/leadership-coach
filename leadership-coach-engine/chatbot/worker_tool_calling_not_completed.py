from typing import Dict, List, Optional

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import NodeWithScore
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore
from config import config

from prompt import CONVERSATIONAL_SYSTEM_PROMPT
from session.manager import SessionManager
from vllm.client import VLLMClient

from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.core.query_engine import RouterQueryEngine, RetrieverQueryEngine
from .web_search import WebSearchTool

from loguru import logger as logging

class ChatbotWorker:
    def __init__(self):
        # chat engine for processing prompts
        self.chat_engine = None

        # create session manager object to manage sessions
        self._session_manager = SessionManager()
        self.router_engine = None

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
            llm = VLLMClient()
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

            youtube_query_engine = RetrieverQueryEngine(
                retriever=retriever,
                node_postprocessors=[similarity_postprocessor]
            )

            # ---- Web Search Tool Query Engine ----
            web_tool = WebSearchTool()
            web_tool_engine = web_tool.to_query_engine()

            # ---- Router Query Engine with LLM decision ----
            tools = [
                QueryEngineTool.from_defaults(
                    query_engine=youtube_query_engine,
                    name="vectordb_engine",
                    description="Answer using YouTube transcript data"
                ),
                QueryEngineTool.from_defaults(
                    query_engine=web_tool_engine,
                    name="web_search",
                    description="Use when YouTube content is insufficient or irrelevant"
                )
            ]

            self._router_engine = RouterQueryEngine(
                selector=LLMSingleSelector.from_defaults(),
                query_engine_tools=tools,
            )

            # self.chat_engine = ContextChatEngine.from_defaults(
            #     retriever=retriever,
            #     node_postprocessors=[similarity_postprocessor],
            #     system_prompt=CONVERSATIONAL_SYSTEM_PROMPT
            # )
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

    async def process_prompt_async(self, session_id: str, user_message: str) -> Dict[str, str]:
        try:
            session = await self._session_manager.get_or_create_session(str(session_id))
            chat_history = session.get()

            history_text = "\n".join(
                [f"{msg.role.value.capitalize()}: {msg.content}" for msg in chat_history[-6:]]
            )
            full_prompt = f"User: {user_message}"

            # First try with RouterQueryEngine
            result = await self._router_engine.aquery(full_prompt)
            answer = result.response if result else ""
            source_nodes = getattr(result, "source_nodes", [])
            sources = []

            # If no context found or response is empty → fallback to direct LLM
            if not answer or not source_nodes:
                system_message = ChatMessage(content=CONVERSATIONAL_SYSTEM_PROMPT, role=MessageRole.SYSTEM)
                messages = [system_message]

                for msg in chat_history[-6:]:
                    if msg.role == MessageRole.ASSISTANT and msg.content == "Empty Response":
                        continue
                    messages.append(msg)

                user_msg = ChatMessage(content=user_message, role=MessageRole.USER)
                messages.append(user_msg)

                chat_response = await self._llm.achat(messages, stop=["user:", "assistant:", "\nuser", "\nassistant"])
                answer = chat_response.message.content if chat_response and chat_response.message else ""
                sources = [{"type": "llm-fallback"}]

            else:
                # Extract YouTube or Web sources
                for node in source_nodes:
                    meta = node.node.metadata
                    if "video_url" in meta:
                        sources.append({
                            "type": "youtube",
                            "title": meta.get("video_title", ""),
                            "url": meta.get("video_url", "")
                        })
                if not sources and "Source:" in answer:
                    parts = answer.split("Source:")
                    answer = parts[0].strip()
                    sources.append({"type": "web", "url": parts[1].strip()})

            await self._session_manager.save_messages(
                session_id=str(session_id),
                user_message=user_message,
                assistant_message=answer
            )

            return {
                "response": str(answer),
                "sources": sources
            }

        except Exception as e:
            logging.error(f"Error processing prompt: {str(e)}")
            return {
                "response": f"Error: {str(e)}",
                "sources": []
            }
