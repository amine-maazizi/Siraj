# server/routes/progress.py
from fastapi import APIRouter
from server.services.progress import get_progress

router = APIRouter(prefix="/progress", tags=["progress"])

@router.get("")
def read_progress():
    return get_progress()
