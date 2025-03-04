#!/bin/bash

# Set the PYTHONPATH to include the current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Set OpenAI API key environment variable if not already set
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Warning: OPENAI_API_KEY environment variable is not set. Please set it or provide it in an .env file."
  
  # Try to load from .env file if it exists
  if [ -f ".env" ]; then
    echo "Loading OpenAI API key from .env file..."
    export $(grep -v '^#' .env | xargs)
  fi
  
  if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: Failed to set OPENAI_API_KEY. Exiting."
    exit 1
  fi
fi

echo "Starting backend server..."
echo "Using Python path: $PYTHONPATH"
echo "Environment: $ENVIRONMENT"

# Set log level to INFO for more detailed logging
export LOG_LEVEL=INFO

# Add timestamp to logs
function timestamp() {
  date +"%Y-%m-%d %H:%M:%S"
}

# Run the FastAPI application with increased log level
cd backend && python -m app.main | while read line; do echo "[$(timestamp)] $line"; done 