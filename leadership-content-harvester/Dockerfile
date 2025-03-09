FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    wget \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ensure all dependencies are installed correctly
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set the entrypoint to run the harvester script
CMD ["python", "main.py"]
