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
    MilvusService,
    EmbeddingService,
    ExcelService
)

from config import get_config, StorageType

PROJECT_DIR = Path(__file__).parent.parent

def process_video(video_data: Dict[str, Any], 
                  transcript_service: TranscriptService,
                  embedding_service: EmbeddingService = None,
                  milvus_service: MilvusService = None,
                  excel_service: ExcelService = None) -> bool:
    """Process a single video: get transcript, generate embeddings, store data."""
    config = get_config()
    video_id = video_data.get("id")
    
    logger.info(f"Attempting to process video: {video_id} - {video_data.get('title', '')}")
    
    if not video_id:
        logger.error("Video data missing ID")
        return False
    
    # Check if video already exists in vector DB (if applicable)
    if config.storage_type in [StorageType.VECTOR_DB, StorageType.BOTH] and milvus_service:
        if milvus_service.video_exists(video_id):
            logger.info(f"Video {video_id} already in database, skipping")
            return False
    
    # Get transcript chunks
    try:
        transcript_chunks = transcript_service.get_chunked_transcript(
            video_id, 
            chunk_size=config.chunk_size, 
            overlap=config.chunk_overlap
        )
        
        if not transcript_chunks:
            logger.warning(f"No transcript chunks retrieved for video {video_id}")
            return False
            
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
            logger.info(f"Storing {len(transcript_data)} chunks for video {video_id} in Excel")
            excel_service.append_transcripts(transcript_data)
        
        # Store in Milvus if configured
        if config.storage_type in [StorageType.VECTOR_DB, StorageType.BOTH] and milvus_service and embedding_service:
            logger.info(f"Generating embeddings for video {video_id}")
            embeddings = embedding_service.generate_embeddings(transcript_chunks)
            
            if embeddings:
                logger.info(f"Storing transcript for video {video_id} in Milvus vector database")
                milvus_service.insert_transcript_chunks(video_data, transcript_chunks, embeddings)
    
    except Exception as e:
        logger.exception(f"Error processing video {video_id}: {e}")
        return False
        
    return True

def load_excel_to_milvus(excel_service: ExcelService, 
                         embedding_service: EmbeddingService, 
                         milvus_service: MilvusService) -> None:
    """Load transcript data from Excel and store it in Milvus vector database."""
    logger.info("Loading transcript data from Excel to Milvus")
    
    # Get transcript data from Excel
    transcript_data = excel_service.load_transcripts()
    
    if not transcript_data or 'Transcripts' not in transcript_data:
        logger.error("No transcript data found in Excel file")
        return
    
    transcripts_df = transcript_data['Transcripts']
    
    # Group by video_id to process each video
    grouped_by_video = transcripts_df.groupby(['video_id', 'video_title', 'video_url'])
    
    processed_count = 0
    for (video_id, video_title, video_url), group in grouped_by_video:
        # Check if video already exists in vector DB
        if milvus_service.video_exists(video_id):
            logger.info(f"Video {video_id} already in database, skipping")
            continue
            
        # Extract transcript chunks
        chunks = group['transcript_chunk'].tolist()
        
        # Create video data dictionary
        video_data = {
            "id": video_id,
            "title": video_title,
            "url": video_url
        }
        
        # Generate embeddings for the chunks
        logger.info(f"Generating embeddings for video {video_id}")
        embeddings = embedding_service.generate_embeddings(chunks)
        
        if embeddings:
            logger.info(f"Storing transcript for video {video_id} in Milvus vector database")
            milvus_service.insert_transcript_chunks(video_data, chunks, embeddings)
            processed_count += 1
        else:
            logger.error(f"Failed to generate embeddings for video {video_id}")
    
    logger.success(f"Successfully processed {processed_count} videos from Excel to Milvus")

def main():
    """Main execution function."""
    # Load config from harvester directory, not project root
    config_path = current_dir / "config.json"
    config = get_config(str(config_path))
    
    logger.info(f"Starting content harvester with storage type: {config.storage_type}")
    
    # Initialize services
    youtube_service = YouTubeService()
    transcript_service = TranscriptService()
    excel_service = ExcelService()
    
    # Only initialize these if needed
    embedding_service = None
    milvus_service = None
    if config.storage_type in [StorageType.VECTOR_DB, StorageType.BOTH]:
        embedding_service = EmbeddingService(model_name=config.embedding_model)
        
        # Simplified MilvusService initialization for standalone Milvus without authentication
        milvus_service = MilvusService(
            uri=config.milvus_uri,
            collection_name=config.milvus_collection_name,
            index_type=config.milvus_index_type if hasattr(config, 'milvus_index_type') else "FLAT",
            index_metric_type=config.milvus_metric_type if hasattr(config, 'milvus_metric_type') else "COSINE"
        )
    
    try:
        # Check if we should load data from Excel to Milvus
        if hasattr(config, 'load_excel_to_milvus') and config.load_excel_to_milvus:
            if excel_service and embedding_service and milvus_service:
                logger.info("Loading data from Excel to Milvus based on config flag")
                load_excel_to_milvus(excel_service, embedding_service, milvus_service)
                return  # Exit after loading data from Excel to Milvus
            else:
                logger.error("Cannot load from Excel to Milvus: required services not initialized")
                return
        
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
            logger.info(f"Created Excel file with {len(videos)} video metadata at {excel_path}")
        
        # Process each video
        processed_count = 0
        skipped_count = 0
        failed_videos = []
        
        for video in videos:
            logger.info(f"Processing video {video.get('id')} - {video.get('title', '')}")
            if process_video(
                video, 
                transcript_service, 
                embedding_service, 
                milvus_service,
                excel_service
            ):
                processed_count += 1
                logger.info(f"Processed {processed_count}/{len(videos)} videos")
            else:
                failed_videos.append(video.get('id'))
                skipped_count += 1
        
        logger.success(f"Processing complete: {processed_count} processed, {skipped_count} skipped/failed")
        if failed_videos:
            logger.warning(f"Failed/skipped videos: {', '.join(failed_videos)}")
        
        # Summary based on storage type
        if config.storage_type == StorageType.EXCEL:
            logger.info(f"Video transcripts saved to Excel. Check {excel_service.default_excel_path}")
        elif config.storage_type == StorageType.VECTOR_DB:
            logger.info(f"Video transcripts stored in Milvus collection: {config.milvus_collection_name}")
        else:
            logger.info(f"Video transcripts saved to both Excel and Milvus collection")
            
    except Exception as e:
        logger.exception(f"Error in content harvesting: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
