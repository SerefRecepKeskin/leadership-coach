"""Module for fastapi initialization"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import include_routers
from services.chat_service import initialize_worker

def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    """
    app = FastAPI(
        title="Leadership Coach API",
        description="A simple API for leadership coaching chatbot.",
        version="0.1.0"
    )

    # Configure CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for POC
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup startup event to initialize worker
    @app.on_event("startup")
    async def startup_event():
        await initialize_worker()

    # Include routes
    include_routers(app)

    return app

app = create_app()
