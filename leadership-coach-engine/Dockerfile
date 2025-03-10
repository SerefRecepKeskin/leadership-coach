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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Create NLTK data directory with proper permissions
RUN mkdir -p /home/appuser/nltk_data && \
    chown -R appuser:appuser /home/appuser/nltk_data

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

# Set NLTK_DATA environment variable to point to user's nltk_data directory
ENV NLTK_DATA=/home/appuser/nltk_data
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 5006

# Run the application
CMD ["python", "server.py"]