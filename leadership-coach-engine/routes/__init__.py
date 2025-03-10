from fastapi import FastAPI
from .chat_route import chat_router
from .health_route import health_router

def include_routers(app: FastAPI):
    """
    Include all routers in the application.
    
    :param app: The FastAPI application
    """
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(health_router)  # No prefix for health check
