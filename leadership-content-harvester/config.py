import os
import json
from enum import Enum
from typing import Dict, Any, Optional
from loguru import logger
import sys
from pathlib import Path

class StorageType(str, Enum):
    """Storage type options."""
    EXCEL = "excel"
    VECTOR_DB = "vector_db" 
    BOTH = "both"

class Config:
    """Configuration for the content harvester."""
    
    def __init__(self, config_path: str = "config.json"):
        # Default configuration
        self.youtube_playlist_id = "PLCi3Q_-uGtdlCsFXHLDDHBSLyq4BkQ6gZ"
        self.weaviate_url = "http://weaviate:8080"
        self.weaviate_collection_name = "LeadershipWisdom"
        self.storage_type = StorageType.EXCEL
        self.batch_size = 10
        self.chunk_size = 1000
        self.chunk_overlap = 100
        self.log_level = "INFO"
        self.data_path = "/data"
        self.excel_output_path = "transcripts.xlsx"
        self.max_videos = 0  # 0 means process all videos
        
        # Load configuration from file
        self.load_config(config_path)
        
        # Setup logging
        self._setup_logging()
    
    def load_config(self, config_path: str) -> None:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    
                    # Get app section if it exists
                    app_config = config_data.get("app", config_data)
                    logger.info(f"Loaded configuration from {config_path}")
                    
                    # Update configuration with values from file
                    for key, value in app_config.items():
                        if hasattr(self, key):
                            # Handle special case for storage_type enum
                            if key == "storage_type":
                                setattr(self, key, StorageType(value))
                            else:
                                setattr(self, key, value)
            else:
                logger.warning(f"Config file {config_path} not found. Using default values.")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
        except Exception as e:
            logger.error(f"Error reading config file: {e}")
    
    def _setup_logging(self) -> None:
        """Setup loguru logger with configured log level."""
        logger.remove()
        logger.add(
            sys.stderr,
            level=self.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )

# Global configuration instance
_config = None

def get_config(config_path: str = "config.json") -> Config:
    """Return global config object, initializing it if needed."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
