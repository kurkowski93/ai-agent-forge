#!/bin/bash

# Function to handle CTRL+C gracefully
function cleanup {
  echo "Shutting down servers..."
  if [ ! -z "$BACKEND_PID" ]; then
    kill $BACKEND_PID
  fi
  if [ ! -z "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID
  fi
  exit 0
}

# Trap SIGINT (CTRL+C)
trap cleanup SIGINT

echo "Starting AgentForge application..."

# Zapisz bieżący katalog jako katalog główny projektu
PROJECT_ROOT=$(pwd)
echo "Project root: $PROJECT_ROOT"

# Check if Python virtual environment exists and activate it
if [ -d "venv" ]; then
  echo "Activating virtual environment..."
  source venv/bin/activate
fi

# Install backend dependencies if needed
if [ ! -d "backend/__pycache__" ]; then
  echo "Installing backend dependencies..."
  pip install -r requirements.txt
  pip install -r backend/requirements.txt
fi

# Start backend server
echo "Starting FastAPI backend server..."
cd backend && python -m app.main &
BACKEND_PID=$!
cd "$PROJECT_ROOT"

# Wait a moment for backend to initialize
sleep 2

# Check if frontend directory exists
if [ -d "$PROJECT_ROOT/frontend" ]; then
  # Start frontend dev server
  echo "Starting frontend development server..."
  cd "$PROJECT_ROOT/frontend"
  
  # Check if node_modules exists, if not, install dependencies
  if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
  fi
  
  echo "Running npm run dev..."
  npm run dev &
  FRONTEND_PID=$!
  cd "$PROJECT_ROOT"
else
  echo "Error: Frontend directory not found at $PROJECT_ROOT/frontend!"
  ls -la "$PROJECT_ROOT"
fi

echo "AgentForge is now running!"
echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop all servers."

# Wait for both processes to finish
wait 