#!/bin/bash

# Set environment variables if needed
export DOCKER_VOLUME_DIRECTORY="./data"

# Ensure the script exits on any error
set -e

echo "Starting Leadership Coach platform..."

# Start everything using docker-compose
docker-compose up -d

echo "Waiting for Milvus to be healthy..."
# Wait for Milvus to be fully operational
until docker-compose exec -T milvus curl -s http://localhost:9091/healthz > /dev/null; do
  echo "Waiting for Milvus to be ready..."
  sleep 5
done

echo "Milvus is ready. Starting data harvesting..."
# Run the content harvester to load data
docker-compose up content-harvester

echo "Data harvesting completed. Starting backend and UI services..."
# Restart the backend and UI services in case they started before harvester completed
docker-compose up -d coach-engine coach-ui

echo "Leadership Coach platform is now running!"
echo "UI available at: http://localhost:8501"
echo "Backend API available at: http://localhost:5006"

# Make the script executable
chmod +x run.sh
