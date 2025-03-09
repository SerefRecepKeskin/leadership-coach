import os
from typing import List, Dict, Any, Optional
import pandas as pd
from loguru import logger
from pathlib import Path
from config import get_config

class ExcelService:
    """Service for handling Excel operations for transcript data storage."""
    
    def __init__(self):
        """Initialize the Excel service with config."""
        self.config = get_config()
        current_dir = Path(__file__).parent.parent.parent
        
        # Handle path properly - ensure we don't treat it as absolute if it doesn't start with /
        data_path = Path(self.config.data_path)
        if not data_path.is_absolute():
            data_path = current_dir / data_path
            
        self.data_dir = data_path
        self.excel_path = data_path / self.config.excel_output_path
        
        # Ensure data directory exists
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Data directory created at {self.data_dir}")
        except OSError as e:
            logger.error(f"Failed to create data directory: {e}")
            # Fallback to a temporary directory in the project folder
            self.data_dir = current_dir / "temp_data"
            self.excel_path = self.data_dir / self.config.excel_output_path
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using fallback data directory: {self.data_dir}")
    
    @property
    def default_excel_path(self) -> str:
        """Return the default Excel file path."""
        return str(self.excel_path)
    
    def save_transcripts(self, videos: List[Dict[str, Any]], transcripts: List[Dict[str, Any]] = None) -> str:
        """
        Create a new Excel file with video metadata and transcripts.
        
        Args:
            videos: List of video metadata dictionaries
            transcripts: List of transcript dictionaries (optional)
            
        Returns:
            Path to the created Excel file
        """
        try:
            # Create Excel writer
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                # Create videos sheet
                video_df = pd.DataFrame(videos)
                video_df.to_excel(writer, sheet_name='Videos', index=False)
                
                # Create transcripts sheet if provided
                if transcripts and len(transcripts) > 0:
                    transcript_df = pd.DataFrame(transcripts)
                    transcript_df.to_excel(writer, sheet_name='Transcripts', index=False)
            
            logger.info(f"Excel file created at {self.excel_path}")
            return str(self.excel_path)
        
        except Exception as e:
            logger.error(f"Error creating Excel file: {e}")
            raise
    
    def append_transcripts(self, transcript_data: List[Dict[str, Any]]) -> None:
        """Append transcript chunks to the Excel file."""
        try:
            if not transcript_data:
                logger.warning("No transcript data to append")
                return
                
            # Check if file exists
            if not self.excel_path.exists():
                logger.info("Excel file doesn't exist, creating new file")
                self.save_transcripts([], transcript_data)
                return
                    
            # Load existing data
            transcript_df = pd.DataFrame(transcript_data)
            logger.info(f"Preparing to append {len(transcript_df)} transcript chunks")
            
            # Check if the Transcripts sheet already exists
            excel_file = pd.ExcelFile(self.excel_path)
            sheet_exists = 'Transcripts' in excel_file.sheet_names
            
            if sheet_exists:
                # Read existing transcripts and append new data
                existing_df = pd.read_excel(self.excel_path, sheet_name='Transcripts')
                logger.info(f"Found existing transcript sheet with {len(existing_df)} rows")
                
                # Check for duplicates
                video_ids = transcript_df['video_id'].unique()
                existing_videos = existing_df['video_id'].unique()
                duplicate_videos = set(video_ids) & set(existing_videos)
                
                if duplicate_videos:
                    logger.warning(f"Found duplicate videos in Excel: {duplicate_videos}")
                
                combined_df = pd.concat([existing_df, transcript_df], ignore_index=True)
                logger.info(f"Combined dataframe has {len(combined_df)} rows")
                
                # Write to Excel with 'replace' mode
                with pd.ExcelWriter(self.excel_path, engine='openpyxl', mode='a', 
                                 if_sheet_exists='replace') as writer:
                    combined_df.to_excel(writer, sheet_name='Transcripts', index=False)
            else:
                logger.info("Creating new Transcripts sheet")
                with pd.ExcelWriter(self.excel_path, engine='openpyxl', mode='a') as writer:
                    transcript_df.to_excel(writer, sheet_name='Transcripts', index=False)
            
            logger.success(f"Successfully added {len(transcript_data)} transcript chunks to {self.excel_path}")
        
        except Exception as e:
            logger.exception(f"Error appending transcripts to Excel file: {e}")
            raise

    def load_transcripts(self) -> Dict[str, pd.DataFrame]:
        """Load transcript data from the Excel file.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary containing DataFrames for each sheet
        """
        try:
            excel_path = Path(self.default_excel_path)
            
            if not excel_path.exists():
                logger.error(f"Excel file not found: {excel_path}")
                return {}
            
            logger.info(f"Loading transcript data from {excel_path}")
            
            # Read all sheets from the Excel file
            sheets = pd.read_excel(excel_path, sheet_name=None)
            
            if not sheets or 'Transcripts' not in sheets:
                logger.error("No 'Transcripts' sheet found in Excel file")
                return {}
            
            logger.info(f"Successfully loaded transcript data from Excel: {len(sheets['Transcripts'])} rows found")
            return sheets
            
        except Exception as e:
            logger.exception(f"Error loading transcript data from Excel: {e}")
            return {}
