from loguru import logger
import sys
import os
from typing import List, Dict, Any
from pathlib import Path

# Fix imports by adding the project root to sys.path if needed
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Now import services using relative imports
from src.services import (
    YouTubeService,
    TranscriptService,
    WeaviateService,
    EmbeddingService,
    ExcelService
)

from config import get_config, StorageType

PROJECT_DIR = Path(__file__).parent.parent

def process_video(video_data: Dict[str, Any], 
                  transcript_service: TranscriptService,
                  embedding_service: EmbeddingService = None,
                  weaviate_service: WeaviateService = None,
                  excel_service: ExcelService = None) -> bool:
    """Process a single video: get transcript, generate embeddings, store data."""
    config = get_config()
    video_id = video_data.get("id")
    
    if not video_id:
        logger.error("Video data missing ID")
        return False
    
    # Check if video already exists in vector DB (if applicable)
    if config.storage_type in [StorageType.VECTOR_DB, StorageType.BOTH] and weaviate_service:
        if weaviate_service.video_exists(video_id):
            logger.info(f"Video {video_id} already in database, skipping")
            return False
    
    # Get transcript chunks
    transcript_chunks = transcript_service.get_chunked_transcript(
        video_id, 
        chunk_size=config.chunk_size, 
        overlap=config.chunk_overlap
    )
     
    logger.info(f"Retrieved {len(transcript_chunks)} transcript chunks for video {video_id}")
    
    # Prepare transcript data for storage
    transcript_data = []
    for i, chunk in enumerate(transcript_chunks):
        transcript_data.append({
            "video_id": video_id,
            "video_title": video_data.get("title", ""),
            "video_url": video_data.get("url", ""),
            "chunk_index": i,
            "transcript_chunk": chunk,
        }) 
    
    # Store in Excel if configured
    if config.storage_type in [StorageType.EXCEL, StorageType.BOTH] and excel_service:
        logger.info(f"Storing transcript for video {video_id} in Excel")
        excel_service.append_transcripts(transcript_data)
    
    # Store in vector DB if configured
    if config.storage_type in [StorageType.VECTOR_DB, StorageType.BOTH] and weaviate_service and embedding_service:
        logger.info(f"Generating embeddings for video {video_id}")
        embeddings = embedding_service.generate_embeddings(transcript_chunks)
        
        if embeddings:
            logger.info(f"Storing transcript for video {video_id} in vector database")
            weaviate_service.insert_transcript_chunks(video_data, transcript_chunks, embeddings)
    
    return True

def main():
    """Main execution function."""
    # Load config from harvester directory, not project root
    config_path = current_dir / "config.json"
    config = get_config(str(config_path))
    
    logger.info(f"Starting content harvester with storage type: {config.storage_type}")
    
    # Initialize services
    youtube_service = YouTubeService()
    transcript_service = TranscriptService()
    excel_service = ExcelService() if config.storage_type in [StorageType.EXCEL, StorageType.BOTH] else None
    
    # Only initialize these if needed
    embedding_service = None
    weaviate_service = None
    if config.storage_type in [StorageType.VECTOR_DB, StorageType.BOTH]:
        embedding_service = EmbeddingService()
        weaviate_service = WeaviateService()
    
    try:
        # Get videos from playlist
        videos = youtube_service.get_playlist_videos(config.youtube_playlist_id)
        
        if not videos:
            logger.error("No videos found in playlist")
            return
        
        logger.info(f"Found {len(videos)} videos in playlist")
        
        # Limit number of videos if specified in config
        if config.max_videos > 0:
            videos = videos[:config.max_videos]
            logger.info(f"Processing only the first {config.max_videos} videos")
        
        # Store all video metadata in Excel if configured
        if config.storage_type in [StorageType.EXCEL, StorageType.BOTH] and excel_service:
            excel_path = excel_service.save_transcripts(videos, [])
            logger.info(f"Created Excel file with video metadata at {excel_path}")
        
        # Process each video
        processed_count = 0
        failed_videos = []
        for video in videos:
            if process_video(
                video, 
                transcript_service, 
                embedding_service, 
                weaviate_service,
                excel_service
            ):
                processed_count += 1
                logger.info(f"Processed {processed_count}/{len(videos)} videos")
            else:
                failed_videos.append(video.get('id'))
        
        logger.success(f"Successfully processed {processed_count} videos")
        if failed_videos:
            logger.warning(f"Failed to process {len(failed_videos)} videos: {', '.join(failed_videos)}")
        
        # Summary based on storage type
        if config.storage_type == StorageType.EXCEL:
            logger.info(f"Video transcripts saved to Excel. Check {excel_service.default_excel_path}")
        elif config.storage_type == StorageType.VECTOR_DB:
            logger.info(f"Video transcripts stored in Weaviate collection: {config.weaviate_collection_name}")
        else:
            logger.info(f"Video transcripts saved to both Excel and Weaviate collection")
            
    except Exception as e:
        logger.exception(f"Error in content harvesting: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
