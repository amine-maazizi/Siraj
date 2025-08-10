from fastapi import APIRouter
from .files import router as files_router
from .ingest import router as ingest_router
from .summarize import router as summarize_router
from .chat import router as chat_router

api = APIRouter()
api.include_router(files_router)
api.include_router(ingest_router)
api.include_router(summarize_router)
api.include_router(chat_router)
