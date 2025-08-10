# server/routes/summarize.py
from fastapi import APIRouter, HTTPException
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..deps import get_vectordb, get_embedding_fn
from server.services.llm import OllamaGenerateClient
import time

router = APIRouter()

# Use the model you actually pulled. You pulled "llama3.1", so use that.
ollama = OllamaGenerateClient(model="llama3.1", host="http://127.0.0.1:11434")

MAP_PROMPT = """You are a teaching assistant. Read the excerpt and produce 2-3 tight bullets capturing the *essential* facts. No fluff, no repetition.
Excerpt:
---
{chunk}
---
Bullets:"""

REDUCE_PROMPT = """Combine the following mini-bullets into a single concise summary with 3-5 bullets total. Merge duplicates, keep it high-level and factual.
Mini-bullets:
---
{points}
---
Final 3-5 bullets:"""

@router.post("/summarize")
def summarize(body: dict):
    doc_id = body.get("doc_id")
    if not doc_id:
        raise HTTPException(400, "doc_id required")

    t0 = time.time()

    seed = "high level summary of this document"
    top_k = 18
    chunks = get_vectordb().similarity_search(seed, k=top_k, filter={"doc_id": doc_id})

    if not chunks:
        return {"summary_sections": [{"title": "Summary", "bullets": ["No content found."]}]}

    bullets = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [
            ex.submit(
                ollama.generate,
                MAP_PROMPT.format(chunk=c.page_content[:1200]),
                0.2,
                220,
            )
            for c in chunks
        ]
        for f in as_completed(futures):
            try:
                bullets.append(f.result())
            except Exception:
                pass

    if time.time() - t0 > 25 and bullets:
        bullets = bullets[:12]

    reduce_text = "\n".join(bullets) if bullets else "No points."
    final = ollama.generate(REDUCE_PROMPT.format(points=reduce_text), 0.2, 260)

    return {
        "summary_sections": [
            {
                "title": "Summary",
                "bullets": [b.strip("-• ").strip() for b in final.split("\n") if b.strip()][:5],
            }
        ]
    }
