from transformers import AutoTokenizer, AutoModel
import torch
from typing import List
from loguru import logger
import numpy as np
from pathlib import Path
from config import get_config

class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize embedding service with a specific model."""
        self.config = get_config()
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_dir = Path(self.config.data_path) / "cache" / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.load_model()
    
    def load_model(self) -> None:
        """Load the embedding model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
            logger.info(f"Model loaded successfully (using {self.device})")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def mean_pooling(self, model_output, attention_mask):
        """Perform mean pooling on token embeddings."""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            logger.warning("Empty list provided for embedding generation")
            return []
            
        try:
            # Tokenize the input texts
            encoded_input = self.tokenizer(
                texts, 
                padding=True, 
                truncation=True, 
                max_length=512, 
                return_tensors='pt'
            ).to(self.device)
            
            # Compute token embeddings
            with torch.no_grad():
                model_output = self.model(**encoded_input)
                
            # Perform mean pooling
            embeddings = self.mean_pooling(model_output, encoded_input['attention_mask'])
            
            # Normalize embeddings
            normalized_embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
            # Convert to list of lists (float values)
            return normalized_embeddings.cpu().numpy().tolist()
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
