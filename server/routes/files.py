# server/routes/files.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


from ..deps import get_vectordb

router = APIRouter(prefix="/files", tags=["files"])

@router.get("/{doc_id}")
def get_pdf(doc_id: str):
    """
    Stream the original PDF for a given doc_id.
    We recover the 'source' path from any chunk's metadata in Chroma.
    """
    vectordb = get_vectordb()
    hits = vectordb.similarity_search("source path lookup", k=1, filter={"doc_id": doc_id})
    if not hits:
        raise HTTPException(status_code=404, detail=f"No file for doc_id={doc_id}")

    src = hits[0].metadata.get("source")
    if not src:
        raise HTTPException(status_code=404, detail="No source path recorded.")

    try:
        return FileResponse(src, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to stream PDF: {e}")
