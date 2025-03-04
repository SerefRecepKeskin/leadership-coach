import weaviate
from weaviate.exceptions import WeaviateBaseError
from loguru import logger
from typing import List, Dict, Any, Optional
import uuid
import time
from config import get_config

class WeaviateService:
    """Service for interacting with Weaviate vector database."""
    
    def __init__(self):
        """Initialize Weaviate service."""
        self.config = get_config()
        self.client = None
        self.connect()
    
    def connect(self) -> None:
        """Connect to Weaviate."""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Connecting to Weaviate at {self.config.weaviate_url}")
                self.client = weaviate.Client(
                    url=self.config.weaviate_url
                )
                if self.client.is_ready():
                    logger.info("Successfully connected to Weaviate")
                    return
                else:
                    raise WeaviateBaseError("Weaviate is not ready")
            except Exception as e:
                retry_count += 1
                wait_time = 2 ** retry_count
                logger.warning(f"Failed to connect to Weaviate (attempt {retry_count}/{max_retries}). Retrying in {wait_time}s. Error: {e}")
                time.sleep(wait_time)
        
        raise ConnectionError(f"Failed to connect to Weaviate after {max_retries} attempts")
    
    def ensure_collection_exists(self) -> None:
        """Create collection if it doesn't exist."""
        collection_name = self.config.weaviate_collection_name
        
        try:
            if not self.client.collections.exists(collection_name):
                logger.info(f"Creating collection {collection_name}")
                
                # Define the collection schema
                self.client.collections.create(
                    name=collection_name,
                    properties=[
                        {
                            "name": "video_id",
                            "dataType": ["text"],
                            "description": "The YouTube video ID",
                        },
                        {
                            "name": "video_title",
                            "dataType": ["text"],
                            "description": "The title of the video",
                        },
                        {
                            "name": "video_author",
                            "dataType": ["text"],
                            "description": "The author/channel of the video",
                        },
                        {
                            "name": "video_url",
                            "dataType": ["text"],
                            "description": "The URL of the video",
                        },
                        {
                            "name": "transcript_chunk",
                            "dataType": ["text"],
                            "description": "A chunk of text from the video transcript",
                            "tokenization": "word",
                            "vectorizePropertyName": True,
                        },
                        {
                            "name": "chunk_index",
                            "dataType": ["int"],
                            "description": "The index of this chunk in the full transcript",
                        },
                        {
                            "name": "publish_date",
                            "dataType": ["date"],
                            "description": "The publish date of the video",
                        }
                    ],
                    vectorizer_config=None,  # We'll provide vectors manually
                )
                logger.info(f"Collection {collection_name} created successfully")
            else:
                logger.info(f"Collection {collection_name} already exists")
        
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise
    
    def insert_transcript_chunks(self, video_data: Dict[str, Any], 
                                transcript_chunks: List[str],
                                vectors: Optional[List[List[float]]] = None) -> List[str]:
        """Insert transcript chunks into Weaviate."""
        collection_name = self.config.weaviate_collection_name
        inserted_ids = []
        
        try:
            # Make sure collection exists
            self.ensure_collection_exists()
            collection = self.client.collections.get(collection_name)
            
            # Insert each chunk
            with collection.batch.dynamic() as batch:
                for i, chunk in enumerate(transcript_chunks):
                    object_id = str(uuid.uuid4())
                    
                    properties = {
                        "video_id": video_data.get("id", ""),
                        "video_title": video_data.get("title", ""),
                        "video_author": video_data.get("author", ""),
                        "video_url": video_data.get("url", ""),
                        "transcript_chunk": chunk,
                        "chunk_index": i,
                        "publish_date": video_data.get("publish_date", ""),
                    }
                    
                    # Add vector if provided
                    if vectors and i < len(vectors):
                        batch.add_object(
                            properties=properties,
                            uuid=object_id,
                            vector=vectors[i]
                        )
                    else:
                        batch.add_object(
                            properties=properties,
                            uuid=object_id
                        )
                    
                    inserted_ids.append(object_id)
            
            logger.info(f"Successfully inserted {len(inserted_ids)} chunks for video {video_data.get('id', '')}")
            return inserted_ids
            
        except Exception as e:
            logger.error(f"Error inserting transcript chunks: {e}")
            return []
    
    def search_by_text(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for transcript chunks by text."""
        collection_name = self.config.weaviate_collection_name
        
        try:
            collection = self.client.collections.get(collection_name)
            
            result = collection.query.near_text(
                query=query_text,
                limit=limit,
            ).do()
            
            objects = result.get("objects", [])
            return [obj["properties"] for obj in objects]
            
        except Exception as e:
            logger.error(f"Error searching for text '{query_text}': {e}")
            return []
    
    def video_exists(self, video_id: str) -> bool:
        """Check if video already exists in the database."""
        collection_name = self.config.weaviate_collection_name
        
        try:
            collection = self.client.collections.get(collection_name)
            
            result = collection.query.get(
                ["video_id"]
            ).with_where({
                "path": ["video_id"],
                "operator": "Equal",
                "valueText": video_id
            }).with_limit(1).do()
            
            return len(result["objects"]) > 0
            
        except Exception as e:
            logger.error(f"Error checking if video {video_id} exists: {e}")
            return False
