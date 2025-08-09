from typing import List
from fastapi import APIRouter, HTTPException

from ..services.llm import OllamaGenerateClient
from ..services.vectorstore import get_vectordb
from ..schemas import SummarizeRequest, SummarizeResponse, SummarySection
from ..utils.json import safe_json_parse
from ..config import (
    CHROMA_DIR, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, OLLAMA_LLM_MODEL,
    SUMMARIZE_TOPK, SUMMARIZE_MAX_MAP_CHUNKS,
)

router = APIRouter(prefix="/summarize", tags=["summarize"])

@router.post("", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    vectordb = get_vectordb(
        persist_directory=str(CHROMA_DIR),
        base_url=OLLAMA_BASE_URL,
        embed_model=OLLAMA_EMBED_MODEL,
    )

    docs = vectordb.similarity_search(
        "Summarize this document.",
        k=SUMMARIZE_TOPK,
        filter={"doc_id": req.doc_id},
    )
    if not docs:
        raise HTTPException(status_code=404, detail=f"No chunks found for doc_id={req.doc_id}")

    try:
        docs.sort(key=lambda d: int(d.metadata.get("chunk_index", 0)))
    except Exception:
        pass

    llm = OllamaGenerateClient(model=OLLAMA_LLM_MODEL, base_url=OLLAMA_BASE_URL)

    map_prompt_tpl = (
        "You are a concise teaching assistant.\n"
        "From the following document chunk, extract 2–3 essential bullet points.\n"
        "Return only plain bullets, one per line, no numbering, no explanations.\n\n"
        "Chunk:\n\"\"\"\n{chunk}\n\"\"\"\n"
    )

    partial_bullets: List[str] = []
    for d in docs[:SUMMARIZE_MAX_MAP_CHUNKS]:
        prompt = map_prompt_tpl.format(chunk=d.page_content[:4000])
        out = llm.generate(prompt, temperature=0.1, num_predict=256)
        for line in out.splitlines():
            line = line.strip().lstrip("-•* ").strip()
            if line:
                partial_bullets.append(line)

    if not partial_bullets:
        raise HTTPException(status_code=500, detail="Map step produced no content.")

    reduce_prompt = (
        "You are a teaching assistant. Combine the following bullets into a concise, sectioned summary.\n"
        "Constraints:\n"
        "- Create 3–5 sections total.\n"
        "- Each section has a short title and 3–5 bullets (clear, factual, non-redundant).\n"
        "- Output STRICT JSON with this schema only:\n"
        '{ "summary_sections": [ { "title": "string", "bullets": ["string", "..."] }, "..."] }\n\n'
        "Bullets:\n"
        + "\n".join([f"- {b}" for b in partial_bullets[:300]])
        + "\n\nReturn ONLY the JSON."
    )

    reduced_text = llm.generate(reduce_prompt, temperature=0.2, num_predict=768)
    data = safe_json_parse(reduced_text)
    if not data or "summary_sections" not in data:
        fallback = SummarySection(title="Summary", bullets=partial_bullets[:8])
        return SummarizeResponse(summary_sections=[fallback])

    try:
        sections = [SummarySection(**s) for s in data["summary_sections"]]
    except Exception:
        sections = [SummarySection(title="Summary", bullets=partial_bullets[:8])]

    return SummarizeResponse(summary_sections=sections)
