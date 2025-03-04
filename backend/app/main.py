import sys
import os
import logging
from pathlib import Path

# Configure logging based on environment variable
log_level_name = os.environ.get('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_name, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized with level: {log_level_name}")

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn

from app.api.agents import router as agents_router

# Ensure configs directory exists
configs_dir = os.path.join(os.getcwd(), "configs")
if not os.path.exists(configs_dir):
    os.makedirs(configs_dir)
    logger.info(f"Created configs directory at {configs_dir}")

app = FastAPI(
    title="AgentForge API",
    description="API for generating and interacting with AI agents",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include our routers
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/api/health", tags=["health"])
async def health_check():
    """
    Health check endpoint to verify the API is running
    """
    logger.debug("Health check endpoint called")
    return {"status": "ok", "message": "API is running"}

if __name__ == "__main__":
    logger.info("Starting API server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 