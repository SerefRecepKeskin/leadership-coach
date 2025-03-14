from typing import List, Union
import numpy as np
import os
import torch
from loguru import logger
from sentence_transformers import SentenceTransformer

# Set the environment variable to avoid tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def get_optimal_device():
    """Determine the optimal device to use for inference on macOS with M1/M2 chips."""
    if torch.backends.mps.is_available():
        logger.info("MPS (Metal Performance Shaders) is available - using M2 Pro neural engine")
        return "mps"
    elif torch.cuda.is_available():
        logger.info("CUDA is available - using GPU")
        return "cuda"
    else:
        logger.info("Using CPU for inference")
        return "cpu"

class EmbeddingService:
    """Service for generating embeddings from text using sentence transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/sentence-t5-base", device: str = None):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name or path of the sentence transformer model
            device: Device to use for inference ('cpu', 'cuda', or 'mps')
                    If None, will automatically select the best device
        """
        # Ensure the environment variable is set
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        # Auto-detect optimal device if none specified
        if device is None:
            device = get_optimal_device()
            
        logger.info(f"Initializing embedding service with model: {model_name} on device: {device}")
        try:
            self.model = SentenceTransformer(model_name, device=device)
            # Set batch size based on device type
            if device == "mps":
                self.batch_size = 24  # Good balance for M2 Pro
            elif device == "cuda":
                self.batch_size = 32  # Larger batch size for GPU
            else:
                self.batch_size = 16  # Default batch size for CPU
                
            logger.info(f"Using batch size: {self.batch_size} for device: {device}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embeddings as numpy arrays
        """
        if not texts:
            logger.warning("Empty text list provided for embedding generation")
            return []
        
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = []
            
            # Process in batches to avoid memory issues
            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i + self.batch_size]
                logger.debug(f"Processing batch {i//self.batch_size + 1} with {len(batch_texts)} texts")
                
                batch_embeddings = self.model.encode(
                    batch_texts, 
                    show_progress_bar=False, 
                    convert_to_numpy=True
                )
                
                # Add batch embeddings to results
                for emb in batch_embeddings:
                    embeddings.append(emb)
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    def generate_embedding(self, text: str) -> Union[np.ndarray, None]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding as numpy array, or None if error occurred
        """
        if not text:
            logger.warning("Empty text provided for embedding generation")
            return None
            
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding for text: {e}")
            return None
