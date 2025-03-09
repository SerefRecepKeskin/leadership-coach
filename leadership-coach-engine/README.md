# Leadership Coach Engine

A Turkish language leadership coaching AI backend service built with FastAPI and LLM technologies. This application provides conversational AI coaching for leadership skills development.

## 🚀 Features

- Conversational AI chatbot specialized in leadership coaching
- Turkish language support
- Context-aware responses using vector search
- Session management for persistent conversations
- Fallback mechanisms for robust response generation

## 🛠️ Technology Stack

- **FastAPI**: Web framework for APIs
- **LLM Integration**: Using VLLM client for language model
- **Vector Store**: Milvus for efficient similarity search
- **Embeddings**: HuggingFace multilingual embeddings
- **Docker**: Containerization support

## 🏗️ Project Structure

```
leadership-coach-engine/
├── app.py                 # FastAPI app initialization
├── server.py              # Server startup script
├── routes/                # API routes definitions
├── services/              # Business logic services
├── schemas/               # Data models/schemas
├── chatbot/               # Chatbot engine implementation
├── session/               # Session management
├── vllm/                  # VLLM client implementation
├── prompt/                # Prompt templates
├── config/                # Configuration files
└── model_cache/           # Cached models
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or newer
- Docker (for containerized deployment)
- Milvus vector database

### Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd leadership-coach-engine
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (if needed)

### Running the Application

**Development mode:**
```bash
python server.py
```

**Docker deployment:**
```bash
docker build -t leadership-coach-engine .
docker run -p 5006:5006 leadership-coach-engine
```

## 📚 API Endpoints

- **GET /chat/welcome**  
  Returns a welcome message when a user starts a new chat session.

- **POST /chat/message**  
  Processes user messages and returns AI-generated responses.

## 🔄 Workflow

1. User sends a message through the API
2. System retrieves relevant leadership context from the vector database
3. Context is combined with chat history and user message
4. LLM generates a response based on the provided context
5. If no relevant context is found, the system falls back to direct LLM interaction
6. The response is returned to the user and conversation history is updated

