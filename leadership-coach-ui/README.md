# Leadership Coach UI

A Streamlit-based user interface for interacting with the AI Leadership Coach assistant.

## Features

- Interactive chat interface with the AI Leadership Coach
- Session management to maintain conversation context
- Error handling for server communication
- Clean and intuitive user interface

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Access to the Leadership Coach backend API

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd leadership-coach/leadership-coach-ui
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running Locally

Start the Streamlit application:

```bash
streamlit run app.py
```

The application will be available at http://localhost:8501

### Using Docker

Build and run the Docker container:

```bash
docker build -t leadership-coach-ui .
docker run -p 8501:8501 leadership-coach-ui
```

## Configuration

The application connects to the Leadership Coach backend API at `http://localhost:5006`. 
If your backend service is running on a different host or port, update the `url` variable in `app.py`.

## Development

### Project Structure

- `app.py` - Main Streamlit application
- `Dockerfile` - Container definition for Docker deployment
- `requirements.txt` - Python dependencies

## Troubleshooting

- If you encounter connection errors, ensure the backend API is running and accessible
- Check logs for detailed error information

## License

[Specify your license here]
