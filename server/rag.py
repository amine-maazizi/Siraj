# server/main.py
import os
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from pypdf import PdfReader

from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# ---- Env / paths
PROJECTS_DIR = Path(os.getenv("SIRAJ_PROJECTS_DIR", "./SirajProjects"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "server/store/chroma"))
DEFAULT_PROJECT = "ExampleProject"  # PoC default

(PROJECTS_DIR / DEFAULT_PROJECT / "resources").mkdir(parents=True, exist_ok=True)
(PROJECTS_DIR / DEFAULT_PROJECT / "media").mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ---- API shape (mirrors shared/schemas.py IngestResponse)
class IngestResponse(BaseModel):
    doc_id: str
    title: str
    pages: int
    chunks: int

app = FastAPI(title="Siraj API")

# CORS: allow your Next.js app at 3000
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
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # 1) Save uploaded PDF locally (local-first storage)
    save_path = PROJECTS_DIR / DEFAULT_PROJECT / "resources" / file.filename
    with open(save_path, "wb") as f:
        f.write(await file.read())

    # 2) Extract text + basic metadata
    reader = PdfReader(str(save_path))
    pages_text: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)

    full_text = "\n".join(pages_text)
    total_pages = len(reader.pages)

    # 3) Chunk for RAG
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=150, separators=["\n\n", "\n", " ", ""]
    )
    docs = splitter.create_documents([full_text], metadatas=[{"source": str(save_path)}])

    # 4) Embeddings via Ollama (make sure the model is pulled)
    #    You can switch to "bge-small" if you prefer.
    embed = OllamaEmbeddings(model="nomic-embed-text")
    # 5) Upsert into persistent Chroma
    vectordb = Chroma(
        collection_name="siraj_docs",
        embedding_function=embed,
        persist_directory=str(CHROMA_DIR),
    )
    # Add chunks; keep a synthetic doc_id to link later features (summary/chat/quiz)
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    # attach doc_id + page-ish hints (optional)
    for i, d in enumerate(docs):
        d.metadata.update({"doc_id": doc_id, "chunk_index": i})

    vectordb.add_texts([d.page_content for d in docs], metadatas=[d.metadata for d in docs])
    vectordb.persist()

    return IngestResponse(
        doc_id=doc_id,
        title=file.filename,
        pages=total_pages,
        chunks=len(docs),
    )
