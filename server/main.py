from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.files import router as files_router
from .docs import router as documents_router
from .routes import api as api_router



app = FastAPI(title="Siraj API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(files_router)
app.include_router(documents_router)

@app.get("/health")
def health():
    return {"ok": True}

