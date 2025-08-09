# server/main.py
import os
import uuid
from pathlib import Path
from typing import List

import requests  # NEW
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

# ---- ENV + dirs
PROJECTS_DIR = Path(os.getenv("SIRAJ_PROJECTS_DIR", "./SirajProjects"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "server/store/chroma"))
DEFAULT_PROJECT = "ExampleProject"  # PoC default for now

(PROJECTS_DIR / DEFAULT_PROJECT / "resources").mkdir(parents=True, exist_ok=True)
(PROJECTS_DIR / DEFAULT_PROJECT / "media").mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ---- Response schema (matches shared/schemas.py)
class IngestResponse(BaseModel):
    doc_id: str
    title: str
    pages: int
    chunks: int

# ---- Minimal embedding client that uses Ollama /api/embed (the one that worked)
class OllamaEmbedViaEmbedRoute:
    """
    Compatible with LangChain's Embeddings interface (embed_documents, embed_query),
    but calls Ollama's /api/embed directly.
    """
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _post_embed(self, inputs: List[str]) -> List[List[float]]:
        try:
            r = requests.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model, "input": inputs},
                timeout=60,
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
            embeddings = data.get("embeddings", [])
            if not embeddings or not isinstance(embeddings, list):
                raise RuntimeError("No embeddings returned from /api/embed")
            return embeddings
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Embedding error: {e}")

    # LangChain contract
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self._post_embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._post_embed([text])[0]

app = FastAPI(title="Siraj API")

# CORS for localhost Next.js (you also have a proxy route; either works)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    name = file.filename or "uploaded.pdf"
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # 1) Save PDF into project resources
    save_path = PROJECTS_DIR / DEFAULT_PROJECT / "resources" / name
    try:
        with open(save_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # 2) Extract text and pages
    try:
        reader = PdfReader(str(save_path))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parse error: {e}")

    pages_text: List[str] = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    full_text = "\n".join(pages_text).strip()
    total_pages = len(reader.pages)

    if not full_text:
        raise HTTPException(status_code=422, detail="No extractable text in PDF.")

    # 3) Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=150, separators=["\n\n", "\n", " ", ""]
    )
    docs = splitter.create_documents([full_text], metadatas=[{"source": str(save_path)}])

    # 4) Embed via working /api/embed route
    embed = OllamaEmbedViaEmbedRoute(
        model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )

    # 5) Persist in Chroma
    vectordb = Chroma(
        collection_name="siraj_docs",
        embedding_function=embed,            # uses our custom class
        persist_directory=str(CHROMA_DIR),
    )

    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    for i, d in enumerate(docs):
        d.metadata.update({"doc_id": doc_id, "chunk_index": i})

    vectordb.add_texts(
        [d.page_content for d in docs],
        metadatas=[d.metadata for d in docs],
    )

    return IngestResponse(
        doc_id=doc_id,
        title=name,
        pages=total_pages,
        chunks=len(docs),
    )
