from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, tools, skills, pipelines, agent, events, tasks, workers, system, tts
from app.core.config import settings
from app.core.exceptions import JarvisException, jarvis_exception_handler
from app.core.lifecycle import lifespan


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Jarvis AI Control Plane Backend Engine",
        lifespan=lifespan,
    )

    # CORS — allow the Next.js frontend to call the backend in dev & via ngrok tunnel
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "https://upstairs-earring-craftwork.ngrok-free.dev",
        ],
        allow_origin_regex=r"^https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(JarvisException, jarvis_exception_handler)

    # Include Routers
    app.include_router(health.router)
    app.include_router(tools.router)
    app.include_router(skills.router)
    app.include_router(pipelines.router)
    app.include_router(agent.router)
    app.include_router(events.router)
    app.include_router(tasks.router)
    app.include_router(workers.router)
    app.include_router(system.router)
    app.include_router(tts.router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
