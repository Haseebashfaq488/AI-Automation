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
from app.modules.drive.helpers.listener import get_drive_listener
from app.modules.memory.service_memory import get_service_memory_manager


async def _periodic_memory_maintenance(interval_seconds: int = 1800):
    """Periodic background task to aggregate daily digests and prune expired 7-day memory."""
    mem_mgr = get_service_memory_manager()
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            mem_mgr.aggregate_daily_digest()
            mem_mgr.prune_expired()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.debug("Memory maintenance background loop error: %s", exc)


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
    drive_listener = get_drive_listener()
    maintenance_task = None

    if not is_testing:
        whatsapp_listener.start()
        gmail_listener.start()
        drive_listener.start()
        maintenance_task = asyncio.create_task(_periodic_memory_maintenance())

    # 5. Pre-warm Antigravity CLI daemon in the background (skip in unit test runs)
    if not is_testing:
        try:
            daemon = get_persistent_agy_daemon()
            asyncio.create_task(daemon.ensure_running())
            logger.info("Pre-warming Persistent Antigravity CLI Daemon...")
        except Exception as exc:
            logger.warning("Could not pre-warm Antigravity CLI daemon: %s", exc)

    # 6. Pre-warm Semantic Vector Embedder in background thread (skip in unit test runs)
    if not is_testing:
        try:
            from app.modules.antigravity.memory_vector_index import prewarm_vector_embedder
            asyncio.create_task(prewarm_vector_embedder())
        except Exception as exc:
            logger.debug("Could not trigger vector embedder pre-warm: %s", exc)

    yield

    logger.info("Shutting down Jarvis Backend Engine...")
    if not is_testing:
        # Stop listeners cleanly
        if maintenance_task:
            maintenance_task.cancel()
        try:
            await whatsapp_listener.stop()
            await gmail_listener.stop()
            await drive_listener.stop()
        except Exception as exc:
            logger.warning("Error stopping inbound listeners: %s", exc)

        try:
            daemon = get_persistent_agy_daemon()
            await daemon.stop()
            logger.info("Persistent Antigravity CLI Daemon stopped cleanly.")
        except Exception as exc:
            logger.warning("Error stopping Antigravity CLI daemon: %s", exc)

