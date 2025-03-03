import sys
import os
from pathlib import Path

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
    print(f"Created configs directory at {configs_dir}")

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

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 