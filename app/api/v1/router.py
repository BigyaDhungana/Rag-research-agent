from fastapi import APIRouter
from app.api.v1 import document, rag, agent

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(document.router)
api_router.include_router(rag.router)
api_router.include_router(agent.router)
