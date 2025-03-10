from fastapi import APIRouter

health_router = APIRouter()

@health_router.get("/healthcheck")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy"}
