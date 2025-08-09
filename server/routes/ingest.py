import uuid
from typing import List
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..schemas import IngestResponse
from ..services.vectorstore import get_vectordb
from ..config import (
    PROJECTS_DIR, DEFAULT_PROJECT, CHROMA_DIR,
    OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    name = file.filename or "uploaded.pdf"
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # 1) Save PDF
    save_path = PROJECTS_DIR / DEFAULT_PROJECT / "resources" / name
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
    docs = splitter.create_documents([full_text], metadatas=[{"source": str(save_path)}])

    # 4) Vector store
    vectordb = get_vectordb(
        persist_directory=str(CHROMA_DIR),
        base_url=OLLAMA_BASE_URL,
        embed_model=OLLAMA_EMBED_MODEL,
    )

    # 5) Add texts
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
