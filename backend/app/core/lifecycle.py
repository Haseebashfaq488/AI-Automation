from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.logging import logger
from app.modules.database.db import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Jarvis Backend Engine...")
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down Jarvis Backend Engine...")
