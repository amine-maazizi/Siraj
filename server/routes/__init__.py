from fastapi import APIRouter
from .files import router as files_router
from .ingest import router as ingest_router
from .summarize import router as summarize_router
from .chat import router as chat_router
from .quiz import router as quiz_router
from .review import router as review_router
from .suggest import router as suggest_router
from .progress import router as progress_router

api = APIRouter()
api.include_router(files_router)
api.include_router(ingest_router)
api.include_router(summarize_router)
api.include_router(chat_router)
api.include_router(quiz_router)
api.include_router(review_router)
api.include_router(suggest_router)
api.include_router(progress_router)