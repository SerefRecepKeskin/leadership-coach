# Leadership Content Harvester

This tool extracts leadership content from YouTube videos, processes the transcripts, and prepares them for use in leadership coaching applications.

## Features

- Download video metadata from YouTube sources
- Extract transcripts from videos
- Process and chunk transcripts for easier consumption
- Clean and format transcripts for better readability
- Convert transcript data to various formats for downstream use

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the example environment file and adjust as needed:
   ```bash
   cp .env.example .env
   ```

## Project Structure

```
leadership-content-harvester/
│
├── data/                      # Data storage directory
│   ├── raw/                   # Raw downloaded transcripts
│   ├── processed/             # Processed transcript files
│   └── metadata/              # Video metadata files
│
├── src/
│   ├── downloaders/           # Content download modules
│   │   ├── __init__.py
│   │   ├── base.py            # Base downloader class
│   │   └── youtube.py         # YouTube-specific downloader
│   │
│   ├── processors/            # Content processing modules
│   │   ├── __init__.py
│   │   ├── base.py            # Base processor class
│   │   ├── cleaner.py         # Text cleaning utilities
│   │   └── chunker.py         # Text chunking utilities
│   │
│   ├── converters/            # Format conversion modules
│   │   ├── __init__.py
│   │   ├── base.py            # Base converter class
│   │   ├── json_converter.py  # JSON output formatter
│   │   └── text_converter.py  # Plain text output formatter
│   │
│   └── main.py                # Main entry point
│
├── .env                       # Environment configuration
├── .env.example               # Example environment configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Configuration

Edit the `.env` file to configure the application:

- `YOUTUBE_API_KEY`: Your YouTube Data API key
- `DATA_DIR`: Path where data files will be stored
- `MAX_VIDEOS`: Maximum number of videos to process at once
- `CHUNK_SIZE`: Number of characters in each transcript chunk
- `CHUNK_OVERLAP`: Number of characters to overlap between chunks

## Usage

Run the harvester:

```bash
python -m src.main
```

### Command Line Arguments

The script supports several command-line arguments:

- `--video-ids`: Comma-separated YouTube video IDs to process
- `--playlist-id`: YouTube playlist ID to process videos from
- `--output-format`: Format for output files (json, text)
- `--clean-only`: Only clean transcripts without chunking
- `--debug`: Enable debug logging

Examples:

```bash
# Process specific videos
python -m src.main --video-ids dQw4w9WgXcQ,jNQXAC9IVRw

# Process videos from a playlist
python -m src.main --playlist-id PLsomething123

# Output as JSON files
python -m src.main --video-ids dQw4w9WgXcQ --output-format json
```

## Extending the Functionality

### Adding New Downloaders

1. Create a new file in `src/downloaders/`
2. Extend the `BaseDownloader` class from `src/downloaders/base.py`
3. Implement the required methods

### Adding New Processors

1. Create a new file in `src/processors/`
2. Extend the `BaseProcessor` class from `src/processors/base.py`
3. Implement the required methods

### Adding New Output Formats

1. Create a new file in `src/converters/`
2. Extend the `BaseConverter` class from `src/converters/base.py`
3. Implement the required methods

## Development

To contribute to development:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Write tests for new functionality
5. Submit a pull request

## License

MIT
