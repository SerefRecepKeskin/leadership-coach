import json
import os
from dataclasses import dataclass
from types import SimpleNamespace
from loguru import logger

@dataclass
class LLMConfig:
    MaxTokens: int
    ApiKey: str
    BaseUrl: str
    
    # Provide backward compatibility with the config.py naming
    @property
    def max_tokens(self):
        return self.MaxTokens
    
    @property
    def api_key(self):
        return self.ApiKey
    
    @property
    def url(self):
        return self.BaseUrl

@dataclass
class EmbeddingsConfig:
    EmbeddingModel: str
    
    # Provide backward compatibility with the config.py naming
    @property
    def model(self):
        return self.EmbeddingModel

@dataclass
class MilvusConfig:
    Uri: str
    User: str
    Password: str
    CollectionName: str
    VectorFieldName: str
    DistanceThreshold: float
    N_Probe: int
    
    # Provide backward compatibility with the config.py naming
    @property
    def uri(self):
        return self.Uri
        
    @property
    def user(self):
        return self.User
        
    @property
    def password(self):
        return self.Password
        
    @property
    def collection_name(self):
        return self.CollectionName
        
    @property
    def vector_field_name(self):
        return self.VectorFieldName
        
    @property
    def distance_threshold(self):
        return self.DistanceThreshold
        
    @property
    def n_probe(self):
        return self.N_Probe
    
    # Legacy properties for backward compatibility
    @property
    def url(self):
        return "localhost"
    
    @property
    def port(self):
        return 19530
    
    @property
    def token(self):
        return "" if not self.User or not self.Password else f"{self.User}:{self.Password}"

@dataclass
class Config:
    llm: LLMConfig
    embeddings: EmbeddingsConfig
    milvus: MilvusConfig
    
    # Legacy property for backward compatibility
    @property
    def embedding(self):
        return SimpleNamespace(
            model=self.embeddings.EmbeddingModel,
            cache_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "model_cache")
        )

def load_config(config_path: str = None) -> Config:
    """Load configuration from the specified JSON file."""
    try:
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "llm-engine-config.json")
            
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Extract configs
        llm_config = config_data.get("LLM", {})
        embeddings_config = config_data.get("Embeddings", {})
        milvus_config = config_data.get("Milvus", {})
        
        return Config(
            llm=LLMConfig(**llm_config),
            embeddings=EmbeddingsConfig(**embeddings_config),
            milvus=MilvusConfig(**milvus_config)
        )
    
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

# Create a singleton instance of Config
config = load_config()
