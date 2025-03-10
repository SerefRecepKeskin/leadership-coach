# Use Python 3.12 as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Add metadata
LABEL maintainer="Leadership Coach Team"
LABEL description="Leadership coaching AI backend service"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Create necessary directories and set permissions
RUN mkdir -p /home/appuser/nltk_data && \
    mkdir -p /home/appuser/.cache/tiktoken && \
    mkdir -p /usr/local/lib/python3.12/site-packages/llama_index/core/_static/tiktoken_cache && \
    chown -R appuser:appuser /home/appuser/nltk_data && \
    chown -R appuser:appuser /home/appuser/.cache && \
    chown -R appuser:appuser /usr/local/lib/python3.12/site-packages/llama_index

# Switch to appuser for downloading NLTK data
USER appuser

# Download NLTK stopwords to the user's home directory
RUN python -c "import nltk; nltk.download('stopwords', download_dir='/home/appuser/nltk_data')"

# Switch back to root to copy the application files
USER root

# Copy the rest of the application
COPY . .

# Change ownership of the application files
RUN chown -R appuser:appuser /app

# Switch to non-root user for running the application
USER appuser

# Set environment variables
ENV NLTK_DATA=/home/appuser/nltk_data
ENV PYTHONUNBUFFERED=1
ENV TIKTOKEN_CACHE_DIR=/home/appuser/.cache/tiktoken

# Expose the port
EXPOSE 5006

# Run the application
CMD ["python", "server.py"]