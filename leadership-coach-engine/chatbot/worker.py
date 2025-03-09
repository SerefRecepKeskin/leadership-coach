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
from .web_search import WebSearchTool


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
            session = await self._session_manager.get_or_create_session(str(session_id))

            # get chat history from the user session
            chat_history = session.get()

            # First try using the chat engine with retrieval
            query_result = await self.chat_engine.achat(
                user_message,
                chat_history=chat_history
            )

            # Check if the response is empty or the sources are empty
            retrieved_nodes = query_result.source_nodes

            # Initialize variables
            answer = ""
            references = []

            # If we got no retrieved context or an empty response, fallback to direct LLM
            if not retrieved_nodes or not query_result.response or query_result.response == "Empty Response":
                # Web search fallback
                web_search_tool = WebSearchTool()
                search_result = web_search_tool.search(user_message)
                
                # Extract URL from search result
                url = search_result.split("Source: ")[-1] if "Source: " in search_result else ""
                if url:
                    references.append({"type": "web", "source": url})
                
                # Combine user message with search results
                enhanced_user_message = f"{user_message}\n\nI did a web search, and here is the result:\n{search_result}"

                # Fallback to direct LLM interaction without retrieval
                llm = Settings.llm
                system_message = ChatMessage(
                    content=CONVERSATIONAL_SYSTEM_PROMPT,
                    role=MessageRole.SYSTEM
                )

                # Construct messages with chat history and the current user message
                messages = [system_message]

                # Add chat history (limited to last few exchanges to save context space)
                chat_history_without_last = chat_history[:-1]
                for msg in chat_history_without_last[-6:]:
                    if msg.role == MessageRole.ASSISTANT and msg.content == "Empty Response":
                        continue
                    messages.append(msg)

                # Add enhanced user message that includes search results
                user_chat_message = ChatMessage(content=enhanced_user_message, role=MessageRole.USER)
                messages.append(user_chat_message)

                # Send directly to LLM with stop tokens
                chat_response = await llm.achat(
                    messages,
                    stop=["user:", "assistant:", "\nuser", "\nassistant"]
                )
                # Explicitly convert to string
                answer = str(
                    chat_response.message.content) if chat_response and chat_response.message and chat_response.message.content else ""
            else:
                # Process vector DB results
                answer = str(query_result.response) if query_result and query_result.response else ""
                
                # Collect video references
                video_refs = set()
                for node in retrieved_nodes:
                    title = node.metadata.get('video_title', 'Unknown Title')
                    url = node.metadata.get('video_url', 'Unknown URL')
                    video_refs.add((title, url))
                
                # Add video references
                for title, url in video_refs:
                    references.append({
                        "type": "video",
                        "title": title,
                        "source": url
                    })

            # Clean up answer
            if answer and "\nuser" in answer:
                answer = answer.split('\nuser')[0]

            # Ensure answer is a string and handle None case
            if answer is None:
                answer = ""

            # Save the conversation to the session
            await self._session_manager.save_messages(
                session_id=str(session_id),
                user_message=user_message,
                assistant_message=answer
            )

            # Return response with references
            return {
                'response': str(answer),
                'references': references
            }

        except Exception as e:
            # Log the error and return an error message
            error_message = f'Error processing message: {str(e)}'
            print(error_message)  # Consider using proper logging instead
            return {
                'response': f"I'm sorry, I encountered an error: {str(e)}",
                'references': []
            }
