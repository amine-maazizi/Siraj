# server/docs.py
from fastapi import APIRouter, Query
from pathlib import Path
from .services.vectorstore import get_vectordb
from .config import CHROMA_DIR, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("")
def list_documents(debug: bool = Query(False)):
    db = get_vectordb(
        persist_directory=str(CHROMA_DIR),
        base_url=OLLAMA_BASE_URL,
        embed_model=OLLAMA_EMBED_MODEL,
    )
    col = db._collection
    count = col.count()
    res = col.get(include=["metadatas"])
    seen = {}
    for meta in (res.get("metadatas") or []):
        if not meta: 
            continue
        did = meta.get("doc_id")
        if not did:
            continue
        title = meta.get("title")
        if not title:
            src = meta.get("source")
            if src:
                title = Path(src).name
        if did not in seen:
            seen[did] = {"doc_id": did, "title": title}
    docs = list(seen.values())

    print("[/documents] CHROMA_DIR=", CHROMA_DIR)
    print("[/documents] count=", count, "unique_docs=", len(docs))
    if debug:
        sample = col.get(include=["metadatas"], limit=3).get("metadatas") or []
        return {"docs": docs, "debug": {"count": count, "sample": sample}}
    return docs
