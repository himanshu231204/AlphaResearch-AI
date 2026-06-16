"""FastAPI application — AlphaResearch AI backend."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.research import router as research_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Graceful shutdown — let in-flight graph executions finish.

    Without this, uvicorn's hard shutdown cancels running asyncio tasks,
    which surfaces as CancelledError inside LangGraph's astream runner.
    """
    logger.info("AlphaResearch AI starting up")
    yield
    # On shutdown: give running tasks a window to complete.
    # Research agents can take several minutes, but 5s is enough for
    # in-progress LLM calls to finish their current response.
    logger.info("AlphaResearch AI shutting down — draining in-flight requests")
    await asyncio.sleep(5)


app = FastAPI(
    title="AlphaResearch AI",
    description="Autonomous AI Equity Research Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "alpha-research-ai"}
