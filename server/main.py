from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.ingest import router as ingest_router
from .routes.summarize import router as summarize_router
from .routes.files import router as files_router


app = FastAPI(title="Siraj API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files_router)


@app.get("/health")
def health():
    return {"ok": True}

# Mount feature routers
app.include_router(ingest_router)
app.include_router(summarize_router)
