# Leadership Content Harvester

A tool for harvesting, processing, and storing leadership content from YouTube videos, specifically designed to work with the Leadership Coach project.

## Overview

This tool extracts transcripts from YouTube videos (either individual videos or entire playlists), processes them into manageable chunks, and stores them in either Excel files, a vector database (Milvus), or both. It can also generate embeddings for the transcript chunks to support semantic search capabilities.

## Features

- Extract transcripts from YouTube videos or playlists
- Process transcripts into manageable chunks with configurable size and overlap
- Generate embeddings for transcript chunks using transformer models
- Store data in Excel format for easy viewing and editing
- Store data in Milvus vector database for semantic search capabilities
- Load data from Excel into Milvus database
- Configurable via JSON configuration file

## Requirements

- Python 3.8 or higher
- Required Python packages (see requirements.txt)
- (Optional) Milvus database for vector storage

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd leadership-coach/leadership-content-harvester
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `config.json` file (see Configuration section below)

## Usage

Run the main script:

```bash
python main.py
```

### Configuration

Create a `config.json` file in the project directory with the following structure:

```json
{
  "app": {
    "youtube_playlist_id": "PLCi3Q_-uGtdlCsFXHLDDHBSLyq4BkQ6gZ",
    "storage_type": "both",
    "batch_size": 10,
    "chunk_size": 1000,
    "chunk_overlap": 100,
    "log_level": "INFO",
    "data_path": "/data",
    "excel_output_path": "transcripts.xlsx",
    "max_videos": 0,
    "load_excel_to_milvus": false,
    "milvus_uri": "http://localhost:19530",
    "milvus_token": "",
    "milvus_user": "",
    "milvus_password": "",
    "milvus_collection_name": "video_transcripts",
    "milvus_index_type": "FLAT",
    "milvus_metric_type": "COSINE",
    "embedding_model": "sentence-transformers/sentence-t5-base"
  }
}
```

#### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `youtube_playlist_id` | ID of the YouTube playlist to process | "PLCi3Q_-uGtdlCsFXHLDDHBSLyq4BkQ6gZ" |
| `storage_type` | Where to store the data (`"excel"`, `"vector_db"`, or `"both"`) | "excel" |
| `batch_size` | Number of videos to process in one batch | 10 |
| `chunk_size` | Size of transcript chunks in characters | 1000 |
| `chunk_overlap` | Overlap between consecutive chunks in characters | 100 |
| `log_level` | Logging level (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`) | "INFO" |
| `data_path` | Path to store data files | "/data" |
| `excel_output_path` | Name of the Excel output file | "transcripts.xlsx" |
| `max_videos` | Maximum number of videos to process (0 = all videos) | 0 |
| `load_excel_to_milvus` | Whether to load data from Excel to Milvus | false |
| `milvus_uri` | URI of the Milvus server | "http://localhost:19530" |
| `milvus_collection_name` | Name of the Milvus collection | "video_transcripts" |
| `milvus_index_type` | Type of index to use in Milvus | "FLAT" |
| `milvus_metric_type` | Metric type for similarity search | "COSINE" |
| `embedding_model` | Transformer model for embedding generation | "sentence-transformers/sentence-t5-base" |

## Project Structure

- `main.py`: Entry point for the application
- `config.py`: Configuration handling
- `/src/services/`: Contains service classes for various functionalities:
  - `YouTubeService`: For fetching video metadata and URLs
  - `TranscriptService`: For extracting and chunking transcripts
  - `EmbeddingService`: For generating embeddings from text
  - `MilvusService`: For interacting with the Milvus vector database
  - `ExcelService`: For storing and loading data from Excel

## Key Functions

- `process_video()`: Processes a single video by extracting transcript, generating embeddings, and storing data
- `load_excel_to_milvus()`: Loads existing transcript data from Excel into the Milvus database
- `main()`: Orchestrates the entire process

## Workflow

1. Load configuration from `config.json`
2. Initialize required services based on configuration
3. If `load_excel_to_milvus` is enabled, load data from Excel to Milvus
4. Otherwise, fetch videos from the specified YouTube playlist
5. For each video:
   - Check if it's already in the database (if using Milvus)
   - Extract and chunk transcript
   - Generate embeddings (if using Milvus)
   - Store data in Excel and/or Milvus
   s