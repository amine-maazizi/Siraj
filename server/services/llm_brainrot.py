# server/services/llm_brainrot.py
from __future__ import annotations
from typing import List, Tuple
from server.services.llm import OllamaGenerateClient
from server.deps import vectordb

OLLAMA = OllamaGenerateClient(model="llama3.1", host="http://127.0.0.1:11434")

def _build_prompt(context: str, style: str, duration_sec: int) -> str:
    # cap words ~140 per 30s
    max_words = max(80, int(140 * (duration_sec / 30)))
    return f"""Write a high-energy, {duration_sec}-second script summarizing the document for a vertical short.
Style = {style}.

Constraints:
- 3 micro-sections: Hook (1–2 lines), Core (4–6 punchy lines), Close (1–2 lines)
- Max {max_words} words total
- Simple language, present tense
- Break lines at natural pauses (one line per caption)

Context (use only what's relevant):
---
{context}
---

Return just the script lines (no labels, no markdown)."""

def brainrot_summary(doc_id: str, style: str = "memetic", duration_sec: int = 30) -> Tuple[str, List[dict]]:
    # pull a few top chunks from this doc for context
    seed = "high level summary of this document"
    chunks = vectordb.similarity_search(seed, k=8, filter={"doc_id": doc_id}) or []
    context = "\n\n".join(c.page_content[:800] for c in chunks)

    prompt = _build_prompt(context, style, duration_sec)
    # NOTE: positional args like in summarize.py → (text, temperature, max_tokens)
    script_text = OLLAMA.generate(prompt, 0.25, 320)

    # Split into lines, then form sections: first 1–2 = Hook, last 1–2 = Close, middle = Core
    lines = [ln.strip() for ln in script_text.splitlines() if ln.strip()]
    hook = lines[:2]
    close = lines[-2:] if len(lines) > 4 else []
    core = lines[2:-2] if len(lines) > 4 else lines[2:]

    sections = [
        {"title": "Hook", "bullets": hook},
        {"title": "Core", "bullets": core},
        {"title": "Close", "bullets": close},
    ]
    return "\n".join(lines), sections
