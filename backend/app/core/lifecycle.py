import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.logging import logger
from app.modules.database.db import engine, Base
from app.workers.antigravity_worker.agent.cli_client import get_persistent_agy_daemon


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Jarvis Backend Engine...")
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Pre-warm Antigravity CLI daemon in the background
    try:
        daemon = get_persistent_agy_daemon()
        asyncio.create_task(daemon.ensure_running())
        logger.info("Pre-warming Persistent Antigravity CLI Daemon...")
    except Exception as exc:
        logger.warning("Could not pre-warm Antigravity CLI daemon: %s", exc)

    yield

    logger.info("Shutting down Jarvis Backend Engine...")
    try:
        daemon = get_persistent_agy_daemon()
        await daemon.stop()
        logger.info("Persistent Antigravity CLI Daemon stopped cleanly.")
    except Exception as exc:
        logger.warning("Error stopping Antigravity CLI daemon: %s", exc)

