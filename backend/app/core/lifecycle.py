import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.logging import logger
from app.modules.database.db import engine, Base
from app.workers.antigravity_worker.agent.cli_client import get_persistent_agy_daemon
from app.core.events.bus import get_event_bus
from app.core.events.orchestrator import get_orchestrator
from app.modules.whatsapp.helpers.listener import get_whatsapp_listener
from app.modules.gmail.helpers.listener import get_gmail_listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Jarvis Backend Engine...")
    # 1. Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # 2. Set current loop on the Global Event Bus
    loop = asyncio.get_running_loop()
    bus = get_event_bus()
    bus.set_loop(loop)

    # 3. Start Task Orchestrator
    orchestrator = get_orchestrator()
    orchestrator.start()

    # 4. Start Inbound Background Listeners (skip in unit test runs)
    import os
    is_testing = bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING"))
    whatsapp_listener = get_whatsapp_listener()
    gmail_listener = get_gmail_listener()

    if not is_testing:
        whatsapp_listener.start()
        gmail_listener.start()

    # 5. Pre-warm Antigravity CLI daemon in the background (skip in unit test runs)
    if not is_testing:
        try:
            daemon = get_persistent_agy_daemon()
            asyncio.create_task(daemon.ensure_running())
            logger.info("Pre-warming Persistent Antigravity CLI Daemon...")
        except Exception as exc:
            logger.warning("Could not pre-warm Antigravity CLI daemon: %s", exc)

    yield

    logger.info("Shutting down Jarvis Backend Engine...")
    if not is_testing:
        # Stop listeners cleanly
        try:
            await whatsapp_listener.stop()
            await gmail_listener.stop()
        except Exception as exc:
            logger.warning("Error stopping inbound listeners: %s", exc)

        try:
            daemon = get_persistent_agy_daemon()
            await daemon.stop()
            logger.info("Persistent Antigravity CLI Daemon stopped cleanly.")
        except Exception as exc:
            logger.warning("Error stopping Antigravity CLI daemon: %s", exc)
