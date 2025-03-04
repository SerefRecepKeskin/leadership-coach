import os
from pytube import Playlist, YouTube
from pytube.exceptions import PytubeError
from loguru import logger
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from config import get_config
import re

class YouTubeService:
    """Service for interacting with YouTube."""
    
    def __init__(self):
        """Initialize YouTube service."""
        self.config = get_config()
        current_dir = Path(__file__).parent.parent.parent
        
        # Handle path properly - ensure we don't treat it as absolute if it doesn't start with /
        data_path = Path(self.config.data_path)
        if not data_path.is_absolute():
            data_path = current_dir / data_path
            
        self.cache_dir = data_path / "cache" / "youtube"
        
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache directory created at {self.cache_dir}")
        except OSError as e:
            logger.error(f"Failed to create cache directory: {e}")
            # Fallback to a temporary directory in the project folder
            self.cache_dir = current_dir / "temp_cache" / "youtube"
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using fallback cache directory: {self.cache_dir}")
            
    def get_playlist_videos(self, playlist_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all videos from a playlist."""
        if playlist_id is None:
            playlist_id = self.config.youtube_playlist_id
            
        logger.info(f"Fetching videos from playlist: {playlist_id}")
        
        cache_file = self.cache_dir / f"playlist_{playlist_id}.json"
        if cache_file.exists():
            logger.info(f"Using cached playlist data from {cache_file}")
            with open(cache_file, "r") as f:
                return json.load(f)
        
        try:
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            playlist = Playlist(playlist_url)
            
            videos = []
            for video_url in playlist.video_urls:
                try:
                    video = YouTube(video_url)
                    
                    # Handle title extraction with fallback mechanism
                    title = self._safe_get_title(video, video_url)
                    
                    # Safe attribute access for all properties
                    views = self._safe_get_views(video)
                    
                    video_data = {
                        "id": video.video_id,
                        "title": title,
                        "url": video_url,
                        "author": getattr(video, "author", "Unknown"),
                        "publish_date": video.publish_date.isoformat() if getattr(video, "publish_date", None) else None,
                        "views": views,
                        "description": getattr(video, "description", ""),
                        "thumbnail_url": getattr(video, "thumbnail_url", ""),
                        "length": self._safe_get_length(video),
                    }
                    videos.append(video_data)
                    logger.debug(f"Retrieved video: {title}")
                except Exception as e:
                    logger.error(f"Error retrieving video {video_url}: {e}")
            
            # Cache the results
            with open(cache_file, "w") as f:
                json.dump(videos, f)
                
            logger.info(f"Successfully retrieved {len(videos)} videos from playlist")
            return videos
            
        except Exception as e:
            logger.error(f"Error fetching playlist {playlist_id}: {e}")
            return []
    
    def _safe_get_title(self, video: YouTube, video_url: str) -> str:
        """Safely get video title with fallback options."""
        try:
            # Try the standard way first
            return video.title
        except (PytubeError, AttributeError, Exception) as e:
            logger.warning(f"Could not get title normally: {e}")
            
            # Fallback 1: Try to extract from URL or video_id
            video_id = video.video_id
            try:
                # If the video has a watch_html attribute, try to extract the title
                if hasattr(video, 'watch_html') and video.watch_html:
                    title_search = re.search(r'<title>(.*?)</title>', video.watch_html)
                    if title_search:
                        title = title_search.group(1).replace(' - YouTube', '')
                        return title
            except Exception as e2:
                logger.warning(f"Fallback 1 failed: {e2}")
            
            # Fallback 2: Just use video ID as title
            logger.info(f"Using video ID as title for {video_url}")
            return f"Video {video_id}"
    
    def _safe_get_views(self, video: YouTube) -> int:
        """Safely get video view count."""
        try:
            # Try to get views directly
            return video.views
        except (PytubeError, AttributeError, TypeError, Exception) as e:
            logger.warning(f"Could not get views normally: {e}")
            
            # Try accessing the raw data
            try:
                if hasattr(video, 'vid_info'):
                    view_count = video.vid_info.get("videoDetails", {}).get("viewCount")
                    if view_count and view_count.isdigit():
                        return int(view_count)
            except Exception as e2:
                logger.warning(f"Fallback for views failed: {e2}")
            
            return 0
    
    def _safe_get_length(self, video: YouTube) -> int:
        """Safely get video length."""
        try:
            return video.length
        except (PytubeError, AttributeError, TypeError, Exception) as e:
            logger.warning(f"Could not get length: {e}")
            return 0
    
    def download_audio(self, video_id: str, download_path: Optional[str] = None) -> Optional[str]:
        """Download audio from a YouTube video using yt-dlp and prepare it for Whisper.
        
        Args:
            video_id: The YouTube video ID
            download_path: Optional custom download directory
            
        Returns:
            Path to downloaded audio file or None if download failed
        """
        # Use provided download path or default to cache directory
        if download_path:
            download_dir = Path(download_path)
        else:
            download_dir = self.cache_dir / "audio"
        
        # Ensure the download directory exists
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Use WAV format with specific parameters optimized for Whisper
        cache_path = download_dir / f"{video_id}.wav"
        
        if cache_path.exists():
            logger.info(f"Using cached audio for video {video_id}")
            return str(cache_path)
        
        try:
            # Import yt-dlp locally to avoid dependency issues if it's not installed
            import yt_dlp
            
            # Configure yt-dlp options optimized for Whisper
            ydl_opts = {
                'format': 'bestaudio/best',  # Get best audio quality
                'outtmpl': str(download_dir / f"{video_id}.%(ext)s"),  # Output file path pattern
                'quiet': True,  # Reduce console output
                'no_warnings': True,  # Suppress warnings
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',  # Extract audio using ffmpeg
                    'preferredcodec': 'wav',      # Convert to WAV format for best Whisper compatibility
                    'preferredquality': '16k',    # 16kHz sampling rate (preferred by Whisper)
                }, {
                    'key': 'FFmpegMetadata',      # Update metadata
                }],
                # Additional FFmpeg parameters for Whisper optimization
                'postprocessor_args': [
                    'FFmpegExtractAudio', '-ar', '16000', '-ac', '1'  # 16kHz sample rate, mono channel
                ],
            }
            
            # Download the audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
            
            # Check if the file was correctly generated with wav extension
            if not cache_path.exists():
                # Look for any file with the video_id prefix
                possible_files = list(download_dir.glob(f"{video_id}.*"))
                if possible_files:
                    downloaded_file = possible_files[0]
                    # Rename to .wav if necessary
                    if downloaded_file.suffix != '.wav':
                        os.rename(downloaded_file, cache_path)
                        logger.info(f"Renamed {downloaded_file} to {cache_path}")
                    else:
                        cache_path = downloaded_file
                else:
                    logger.error(f"No output file found for video {video_id}")
                    return None
            
            logger.info(f"Audio downloaded for video {video_id} to {cache_path} (optimized for Whisper)")
            return str(cache_path)
        
        except ImportError:
            logger.error("yt-dlp is not installed. Install it with: pip install yt-dlp")
            return None
        except Exception as e:
            logger.error(f"Error downloading audio for video {video_id}: {e}")
            return None