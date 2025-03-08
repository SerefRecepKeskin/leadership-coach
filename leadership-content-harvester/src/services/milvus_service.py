import re
from datetime import datetime
from typing import Any, Dict, List, Union

import pandas as pd

from numpy import ndarray
from sentence_transformers import SentenceTransformer
from torch import Tensor

from loguru import logger
from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient
import numpy as np

class MilvusService:
    """
    Service for handling Milvus vector database operations for transcript chunks.
    """
    
    def __init__(
        self,
        uri: str,
        user: str = None,
        password: str = None,
        token: str = None,
        collection_name: str = 'video_transcripts',
        index_type: str = 'FLAT',
        index_metric_type: str = 'COSINE',
        index_params: Dict[str, Union[str, float, int, Any]] = None,
    ):
        """
        Initialize MilvusService
        
        Args:
            uri: Milvus server URI
            user: Milvus username for authentication
            password: Milvus password for authentication
            token: Milvus authentication token (if not using username/password)
            collection_name: Name of the collection for storing transcript chunks
            index_type: Type of index to use (FLAT, IVF_FLAT, etc.)
            index_metric_type: Type of distance metric (COSINE, L2, IP)
            index_params: Additional index parameters
        """
        self._client = None
        self._collection_name = collection_name
        self._index_type = index_type
        self._index_metric_type = index_metric_type
        self._index_params = {'nlist': 256} if index_params is None else index_params
        self._fields = [
            FieldSchema(name='id', dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name='video_id', dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name='video_title', dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name='video_url', dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name='chunk_index', dtype=DataType.INT64),
            FieldSchema(name='transcript_chunk', dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name='transcript_vector', dtype=DataType.FLOAT_VECTOR, dim=768)
        ]

        # Initialize Milvus client with appropriate authentication method
        if user and password:
            self._client = MilvusClient(
                uri=uri,
                user=user,
                password=password
            )
            logger.info(f"Connecting to Milvus at {uri} with username/password authentication")
        elif token:
            self._client = MilvusClient(
                uri=uri,
                token=token
            )
            logger.info(f"Connecting to Milvus at {uri} with token authentication")
        else:
            self._client = MilvusClient(uri=uri)
            logger.info(f"Connecting to Milvus at {uri} without authentication")
        
        # Create collection if it doesn't exist
        self._ensure_collection_exists()
        
    def _ensure_collection_exists(self) -> None:
        """
        Check if collection exists, if not create it with the appropriate schema and index
        """
        try:
            collections = self._client.list_collections()
            if self._collection_name not in collections:
                self._create_collection()
            else:
                logger.info(f"Collection {self._collection_name} already exists")
                # Load collection into memory
                self._client.load_collection(self._collection_name)
        except Exception as e:
            logger.error(f"Error checking collection existence: {str(e)}")
            raise

    def _create_collection(self) -> None:
        """
        Create collection with schema and index
        """
        try:
            schema = CollectionSchema(
                fields=self._fields,
                auto_id=True,
                enable_dynamic_field=True
            )

            logger.info(f'Creating Milvus collection: {self._collection_name}')
            self._client.create_collection(
                collection_name=self._collection_name,
                schema=schema,
            )
            
            # Create index on transcript_vector field - fixed to use prepare_index_params properly
            logger.info('Creating index on transcript_vector field...')
            
            # Use the prepare_index_params method to create the correct index parameters
            index_params = self._client.prepare_index_params()
            index_params.add_index(
                field_name="transcript_vector",
                index_type=self._index_type,
                metric_type=self._index_metric_type,
                params=self._index_params
            )
            
            self._client.create_index(
                collection_name=self._collection_name,
                index_params=index_params
            )
            logger.info('Index created successfully')
            
            # Load collection into memory
            self._client.load_collection(self._collection_name)
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise

    def video_exists(self, video_id: str) -> bool:
        """
        Check if a video already exists in the collection
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            bool: True if video exists, False otherwise
        """
        try:
            results = self._client.query(
                collection_name=self._collection_name,
                filter=f'video_id == "{video_id}"',
                output_fields=["video_id"],
                limit=1
            )
            return len(results) > 0
        except Exception as e:
            logger.error(f"Error checking if video exists: {str(e)}")
            return False

    def insert_transcript_chunks(
        self,
        video_data: Dict[str, str],
        transcript_chunks: List[str],
        embeddings: List[np.ndarray]
    ) -> None:
        """
        Insert transcript chunks with their embeddings into Milvus
        
        Args:
            video_data: Dictionary containing video metadata
            transcript_chunks: List of transcript chunk texts
            embeddings: List of transcript chunk embeddings
        """
        if len(transcript_chunks) != len(embeddings):
            raise ValueError("Number of transcript chunks must match number of embeddings")
        
        video_id = video_data.get('id')
        video_title = video_data.get('title', '')
        video_url = video_data.get('url', '')

        records = []
        
        try:
            for i, (chunk, embedding) in enumerate(zip(transcript_chunks, embeddings)):
                # Handle any potential issues with embeddings format
                if not isinstance(embedding, list):
                    embedding_list = embedding.tolist()
                else:
                    embedding_list = embedding
                    
                records.append({
                    'id': f"{video_id}_{i}",  # Create a unique ID per chunk
                    'video_id': video_id,
                    'video_title': video_title,
                    'video_url': video_url,
                    'chunk_index': i,
                    'transcript_chunk': chunk,
                    'transcript_vector': embedding_list
                })
            
            if records:
                logger.info(f'Inserting {len(records)} transcript chunks for video {video_id}')
                self._client.insert(
                    collection_name=self._collection_name,
                    data=records
                )
                logger.info(f'Successfully inserted transcript chunks for video {video_id}')
            else:
                logger.warning(f'No records to insert for video {video_id}')
                
        except Exception as e:
            logger.error(f"Error inserting transcript chunks: {str(e)}")
            raise
    
    def search_similar_chunks(
        self, 
        query_embedding: np.ndarray,
        limit: int = 5,
        output_fields: List[str] = None
    ) -> List[Dict]:
        """
        Search for similar transcript chunks
        
        Args:
            query_embedding: Embedding vector of the query
            limit: Maximum number of results to return
            output_fields: Fields to include in the search results
            
        Returns:
            List of dictionaries containing search results
        """
        if output_fields is None:
            output_fields = [
                'video_id', 'video_title', 'video_url', 
                'chunk_index', 'transcript_chunk'
            ]
            
        try:
            # Convert embedding to list if it's not already
            if not isinstance(query_embedding, list):
                query_embedding_list = query_embedding.tolist()
            else:
                query_embedding_list = query_embedding
                
            search_params = {
                "metric_type": self._index_metric_type,
                "params": {"nprobe": 10}
            }
            
            search_result = self._client.search(
                collection_name=self._collection_name,
                data=[query_embedding_list],
                anns_field="transcript_vector",
                param=search_params,
                limit=limit,
                output_fields=output_fields
            )
            
            # Return the results from the first query
            return search_result[0]
        except Exception as e:
            logger.error(f"Error during vector search: {str(e)}")
            return []