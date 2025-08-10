# server/routes/ingest.py
import uuid
from typing import List
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..schemas import IngestResponse
from ..deps import get_vectordb
from ..config import (
    PROJECTS_DIR, DEFAULT_PROJECT,
    OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    name = file.filename or "uploaded.pdf"
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # 1) Save PDF (make sure dirs exist)
    proj_dir = PROJECTS_DIR / DEFAULT_PROJECT / "resources"
    proj_dir.mkdir(parents=True, exist_ok=True)
    save_path = proj_dir / name
    try:
        with open(save_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # 2) Extract text
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
    # seed metadata with source, title now
    docs = splitter.create_documents(
        [full_text],
        metadatas=[{"source": str(save_path), "title": name}],
    )

    # 4) Vector store
    vectordb = get_vectordb()

    # 5) Add texts with doc_id + chunk_index
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    for i, d in enumerate(docs):
        d.metadata.update({
            "doc_id": doc_id,
            "chunk_index": i,
            # keep title in every chunk so /docs can find it reliably
            "title": name,
        })

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
