# Leadership Coach

**Note: This project is a basic proof of concept (POC) and does not include any security measures. It is not suitable for production use.**

**Note: This project uses an open-source model served by vLLM. Minor changes to the client are required to use OpenAI models.**

An AI-powered leadership coaching platform that provides personalized leadership advice based on expert content.

## Overview

Leadership Coach is a complete system designed to help professionals improve their leadership skills through AI-assisted coaching. The platform processes leadership content from various sources, organizes this knowledge in a vector database, and delivers personalized advice through a conversational interface.

## Architecture

The system consists of three main components:

1. **Content Harvester**: Collects, processes, and indexes leadership content from various sources including YouTube videos
2. **Coach Engine**: Backend API service that powers the conversational AI using retrieval-augmented generation
3. **Coach UI**: Streamlit-based user interface for interacting with the coaching system

## Prerequisites

- Docker and Docker Compose
- 8+ GB of RAM available for Docker
- Internet connection for model downloads
- Approximately 10GB of free disk space

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/SerefRecepKeskin/leadership-coach.git
   cd leadership-coach
   ```

2. Run the setup script:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

3. Access the UI at [http://localhost:8501](http://localhost:8501)

## Components

### 1. Leadership Content Harvester

The harvester collects and processes leadership content:
- YouTube video transcription
- Text processing and chunking
- Vector embedding generation
- Storage in Milvus vector database

### 2. Leadership Coach Engine

FastAPI backend that provides:
- Conversational AI interface
- Context-aware responses using RAG (Retrieval Augmented Generation)
- Session management for continuing conversations
- Integration with language models

### 3. Leadership Coach UI

Streamlit-based frontend offering:
- Clean, user-friendly chat interface
- Conversation history tracking
- Leadership topic selection
- Mobile-friendly design

## Data Flow

1. Content is harvested from leadership sources and stored in Milvus
2. User asks a leadership question via the UI
3. Coach Engine retrieves relevant context from the vector database
4. LLM generates a response using the context and conversation history
5. Response is returned to the user through the UI

## Configuration

The system can be configured through:
- Environment variables in docker-compose.yml
- Config files in each component's directory
- LLM settings in coach-engine/config/

### LLM Engine Configuration

The `llm-engine-config.json` file is used to configure the LLM engine. Below is the structure of the file and the fields that need to be set:

```json
{
  "LLM": {
    "MaxTokens": 600,  // Maximum number of tokens for the model to generate
    "ApiKey": "your_api_key_here",  // API key for authentication
    "BaseUrl": "http://your_vllm_server_url"  // Base URL of the vLLM server
  },
  "Embeddings": {
    "EmbeddingModel": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  // Model used for generating embeddings
  },
  "Milvus": {
    "Uri": "http://localhost:19530",  // URI of the Milvus server
    "User": "",  // Username for Milvus (if applicable)
    "Password": "",  // Password for Milvus (if applicable)
    "CollectionName": "Video_transcripts",  // Name of the collection in Milvus
    "VectorFieldName": "transcript_vector",  // Name of the vector field in the collection
    "DistanceThreshold": 0.80,  // Distance threshold for vector similarity search
    "N_Probe": 16  // Number of probes for the search
  }
}
```

Ensure that you set the `ApiKey` and `BaseUrl` fields under the `LLM` section to match your vLLM server configuration.

## Troubleshooting

**Common Issues:**

- **Milvus connection errors**: Check if Milvus container is healthy with `docker-compose ps`
- **Content not loading**: Check harvester logs with `docker-compose logs content-harvester`
- **UI not connecting to backend**: Ensure coach-engine service is running and healthy

## Development

To work on individual components:

1. **Content Harvester**:
   ```bash
   cd leadership-content-harvester
   pip install -r requirements.txt
   python main.py
   ```

2. **Coach Engine**:
   ```bash
   cd leadership-coach-engine
   pip install -r requirements.txt
   python server.py
   ```

3. **Coach UI**:
   ```bash
   cd leadership-coach-ui
   pip install -r requirements.txt
   streamlit run app.py
   ```
