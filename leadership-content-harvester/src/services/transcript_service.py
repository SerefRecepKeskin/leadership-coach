from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from loguru import logger
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from config import get_config
import subprocess
import os
import shutil
import sys
from .youtube_service import YouTubeService  # Import YouTubeService

class TranscriptService:
    """Service for retrieving and processing video transcripts."""
    
    def __init__(self):
        """Initialize transcript service."""
        self.config = get_config()
        current_dir = Path(__file__).parent.parent.parent
        
        # Initialize YouTube service for audio downloading
        self.youtube_service = YouTubeService()
        
        # Handle path properly - ensure we don't treat it as absolute if it doesn't start with /
        data_path = Path(self.config.data_path)
        if not data_path.is_absolute():
            data_path = current_dir / data_path
            
        self.cache_dir = data_path / "cache" / "transcripts"
        # Create a dedicated audio cache folder
        self.audio_cache_dir = data_path / "cache" / "audio"
        
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.audio_cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Transcript cache directory created at {self.cache_dir}")
            logger.info(f"Audio cache directory created at {self.audio_cache_dir}")
        except OSError as e:
            logger.error(f"Failed to create cache directories: {e}")
            # Fallback to temporary directories in the project folder
            self.cache_dir = current_dir / "temp_cache" / "transcripts"
            self.audio_cache_dir = current_dir / "temp_cache" / "audio"
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.audio_cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using fallback cache directories: {self.cache_dir} and {self.audio_cache_dir}")
    
    def get_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript for a video."""
        cache_file = self.cache_dir / f"{video_id}.json"
        
        if cache_file.exists():
            logger.info(f"Using cached transcript for video {video_id}")
            with open(cache_file, "r") as f:
                transcript_data = json.load(f)
                return self._format_transcript(transcript_data)
        
        try:
            logger.info(f"Retrieving transcript for video {video_id}")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Cache the transcript data
            with open(cache_file, "w") as f:
                json.dump(transcript_list, f)
            
            return self._format_transcript(transcript_list)
            
        except TranscriptsDisabled:
            logger.warning(f"Transcripts are disabled for video {video_id}, trying alternative methods")
            # First try translated caption approach
            transcript = self._try_translated_transcripts(video_id, cache_file)
            if transcript:
                return transcript
            
            # Then try auto-generated transcripts as a fallback
            transcript = self._try_auto_transcript(video_id, cache_file)
            if transcript:
                return transcript
                
            # Last resort: extract audio and transcribe it
            logger.warning(f"All transcript retrieval methods failed for {video_id}, attempting audio extraction and transcription")
            return self._extract_and_transcribe_audio(video_id, cache_file)
            
        except NoTranscriptFound:
            logger.warning(f"No standard transcript found for video {video_id}, trying auto-generated ones")
            transcript = self._try_auto_transcript(video_id, cache_file)
            if transcript:
                return transcript
                
            # Last resort: extract audio and transcribe it
            logger.warning(f"Auto-transcript retrieval failed for {video_id}, attempting audio extraction and transcription")
            return self._extract_and_transcribe_audio(video_id, cache_file)
            
        except Exception as e:
            logger.error(f"Error retrieving transcript for video {video_id}: {e}")
            
            # Try audio extraction as a last resort
            try:
                logger.info(f"Attempting audio extraction and transcription for {video_id}")
                return self._extract_and_transcribe_audio(video_id, cache_file)
            except Exception as e2:
                logger.error(f"Audio extraction failed for {video_id}: {e2}")
                return None
    
    def _try_translated_transcripts(self, video_id: str, cache_file: Path) -> Optional[str]:
        """Try to get transcripts through YouTube's translation feature."""
        # Focus only on Turkish
        target_language = 'tr'
        
        logger.info(f"Attempting to retrieve Turkish transcript via translation feature for video {video_id}")
        
        try:
            # Get transcript list with translation languages
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Look for any available transcript we can translate to Turkish
            for transcript in transcript_list:
                try:
                    # Try to translate to Turkish
                    translated = transcript.translate(target_language)
                    data = translated.fetch()
                    
                    # Cache the successful transcript
                    with open(cache_file, "w") as f:
                        json.dump(data, f)
                    
                    logger.info(f"Found translated transcript via {transcript.language_code} → {target_language} for video {video_id}")
                    return self._format_transcript(data)
                except Exception as e:
                    logger.debug(f"Failed to translate transcript {transcript.language_code} to Turkish: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"Failed to list available transcripts: {e}")
        
        logger.warning(f"Could not retrieve transcript via translation for video {video_id}")
        return None
    
    def _try_auto_transcript(self, video_id: str, cache_file: Path) -> Optional[str]:
        """Try to get auto-generated transcripts in Turkish."""
        try:
            logger.info(f"Trying to get auto-generated Turkish transcript for video {video_id}")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['tr'])
            
            # Cache the successful transcript
            with open(cache_file, "w") as f:
                json.dump(transcript_list, f)
            
            logger.info(f"Found auto-generated Turkish transcript for video {video_id}")
            return self._format_transcript(transcript_list)
        except Exception as e:
            logger.debug(f"Could not get Turkish auto transcript: {e}")
            return None
    
    def _extract_and_transcribe_audio(self, video_id: str, cache_file: Path) -> Optional[str]:
        """Extract audio from YouTube video and transcribe it using speech recognition."""
        logger.info(f"Extracting audio for video {video_id} using YouTubeService")
        
        # Use YouTubeService to download the audio, specifying the audio cache directory
        audio_file_path = self.youtube_service.download_audio(
            video_id, 
            download_path=str(self.audio_cache_dir)
        )
        
        if not audio_file_path:
            logger.error(f"Failed to download audio for video {video_id}")
            return None
            
        # Verify the file exists and has content before transcription
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file does not exist at {audio_file_path}")
            return None
            
        if os.path.getsize(audio_file_path) == 0:
            logger.error(f"Audio file is empty at {audio_file_path}")
            return None
        
        # Transcribe the audio (now WAV format optimized for Whisper)
        return self._transcribe_with_whisper(audio_file_path, video_id, cache_file)
    
    def _transcribe_with_whisper(self, audio_file: str, video_id: str, cache_file: Path) -> Optional[str]:
        """Transcribe audio using OpenAI's Whisper (requires whisper package)."""
        try:
            # Check if file exists before attempting transcription
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found at {audio_file}")
                return None
                
            # Try to import whisper
            import whisper
            
            logger.info(f"Transcribing audio with Whisper for {video_id}")
            
            # Load Whisper model - choose a smaller model for faster processing
            model = whisper.load_model("base")
            
            # The audio is already optimized for Whisper (WAV 16kHz mono)
            # so we can directly transcribe it without additional preprocessing
            result = model.transcribe(
                audio_file, 
                language="tr",     # Turkish language hint
                fp16=False         # Set to True if you have GPU with FP16 support
            )
            
            # Format the result
            text = result.get("text", "")
            
            if text:
                # Create transcript data in the expected format
                transcript_data = [{"text": text, "start": 0.0, "duration": 0.0}]
                
                # Cache the transcript
                with open(cache_file, "w") as f:
                    json.dump(transcript_data, f)
                
                logger.info(f"Successfully transcribed WAV audio for {video_id} using Whisper")
                return text.strip()
            else:
                logger.warning(f"Whisper returned empty transcript for {video_id}")
                return None
                
        except ImportError:
            logger.error("Whisper package not installed. Install with: pip install openai-whisper")
            return None
        except Exception as e:
            logger.error(f"Whisper transcription failed for {video_id}: {e}")
            logger.exception("Full exception details:")
            return None
    
    def _format_transcript(self, transcript_data: List[Dict[str, Any]]) -> str:
        """Format transcript data into a readable string."""
        formatted_text = ""
        
        for item in transcript_data:
            text = item.get("text", "").strip()
            if text:
                formatted_text += f"{text} "
        
        return formatted_text.strip()
    
    def get_chunked_transcript(self, video_id: str, chunk_size: int = 1000, 
                              overlap: int = 100) -> List[str]:
        """Get transcript in chunks for better processing."""
        full_transcript = self.get_transcript(video_id)
        
        if not full_transcript:
            return []
            
        chunks = []
        for i in range(0, len(full_transcript), chunk_size - overlap):
            chunk = full_transcript[i:i + chunk_size]
            if chunk:
                chunks.append(chunk)
                
        logger.info(f"Split transcript into {len(chunks)} chunks")
        return chunks
