# Use Python 3.10 as base image
FROM python:3.10-slim

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

# Download NLTK stopwords
RUN python -m nltk.downloader stopwords

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 5006

# Define environment variables (override at runtime)
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Run the application
CMD ["python", "server.py"]
