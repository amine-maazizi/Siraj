# server/routes/suggest.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from server.services.llm import OllamaGenerateClient
from server.services import attempts as attempt_store
from ddgs import DDGS  # pip install ddgs

router = APIRouter(prefix="")

# ---------- Schemas ----------
class SuggestReq(BaseModel):
    gaps: List[str] = Field(default_factory=list)         # e.g. ["Newton's 2nd Law", "Kinematics graphs"]
    time_per_day: int = 30                                # minutes
    horizon_weeks: int = 4
    doc_id: Optional[str] = None                          # optional: bias against a doc

class Task(BaseModel):
    text: str
    reason: Optional[str] = None
    effort_min: Optional[int] = None

ResourceType = Literal["book", "pdf", "video", "course", "article"]
class Resource(BaseModel):
    title: str
    type: ResourceType
    link: str
    price: Optional[str] = None                           # "Free", "$19", etc.
    provider: Optional[str] = None                        # "YouTube", "MIT OCW", "O’Reilly", etc.
    embed_url: Optional[str] = None                       # for videos/PDFs

class SuggestResp(BaseModel):
    tasks: List[Task]
    resources: List[Resource]

# ---------- Helpers ----------
def _youtube_embed(url: str) -> Optional[str]:
    # supports common formats
    import re
    pat = r"(?:v=|youtu\.be/|embed/)([\w\-]{11})"
    m = re.search(pat, url)
    return f"https://www.youtube-nocookie.com/embed/{m.group(1)}" if m else None

def _pdf_embed(url: str) -> Optional[str]:
    # Most browsers render PDFs natively; let the client <iframe> it
    return url if url.lower().endswith(".pdf") else None

# server/routes/suggest.py
def _mine_gaps_from_attempts(limit:int=10) -> list[str]:
    atts = attempt_store.get_attempts(limit=limit)
    topics, wrong_texts = [], []
    for a in atts:
        for q in a.get("per_question", []):
            if not isinstance(q, dict): 
                continue
            # take explicit topics if present
            for key in ("topic","tag"):
                v = q.get(key)
                if isinstance(v, str) and v.strip():
                    topics.append(v.strip())
            # collect stems/rationales for wrong items
            if q.get("correct") is False:
                if q.get("question"): wrong_texts.append(q["question"])
                if q.get("rationale"): wrong_texts.append(q["rationale"])
    # prefer explicit topics; else condense wrong_texts via LLM
    if topics:
        # dedupe
        seen=set(); out=[]
        for t in topics:
            tl=t.lower()
            if tl in seen: continue
            seen.add(tl); out.append(t)
        return out[:8]
    if wrong_texts:
        llm = OllamaGenerateClient(model="llama3.1")
        return _condense_topics_with_llm(llm, wrong_texts)
    return []


def _condense_topics_with_llm(llm: OllamaGenerateClient, texts: list[str]) -> list[str]:
    joined = "\n".join(f"- {t}" for t in texts) or "None."
    prompt = f"""You are a strict topic normalizer for study gaps.
Input list (possibly noisy/duplicated):
{joined}

Return 5-8 normalized, distinct core topics (one per line), no numbering, concise."""
    out = llm.generate(prompt, temperature=0.2, num_predict=256)
    topics = [line.strip("- ").strip() for line in out.splitlines() if line.strip()]
    # keep short phrases only
    topics = [t for t in topics if 2 <= len(t) <= 80][:8]
    return topics or texts[:6]

def _make_tasks_with_llm(llm: OllamaGenerateClient, topics: list[str], time_per_day: int, horizon_weeks: int) -> list[Task]:
    # Ask LLM for atomic to-dos (not weekly plan—just a backlog)
    prompt = f"""Create a focused backlog of 8–14 atomic study tasks from these weak topics:
{chr(10).join(f"- {t}" for t in topics)}

Constraints:
- Each task fits in {time_per_day} minutes or less.
- Mix: short theory reviews, 5–10 problem sets, micro-summaries, flashcards.
- Be concrete (numbers, chapters, pages).
Return as lines: task — reason — effort_min.
Example: "Solve 5 kinematics graph questions — solidify slope/area intuition — 25"
"""
    out = llm.generate(prompt, temperature=0.2, num_predict=512)
    tasks: list[Task] = []
    for line in out.splitlines():
        line = line.strip(" -\t")
        if not line:
            continue
        # naive parse: "text — reason — minutes"
        parts = [p.strip() for p in line.split("—")]
        text = parts[0] if parts else ""
        reason = parts[1] if len(parts) > 1 else None
        mins = None
        if len(parts) > 2:
            try:
                mins = int("".join(ch for ch in parts[2] if ch.isdigit()))
            except:
                mins = None
        if text:
            tasks.append(Task(text=text, reason=reason, effort_min=mins))
    # clamp length
    return tasks[:14] if tasks else [Task(text="Review core definitions", effort_min=min(25, time_per_day))]


def _search_resources(topics: list[str], max_per_kind: int = 2) -> list[Resource]:
    # Free + pragmatic search using duckduckgo_search
    results: list[Resource] = []
    with DDGS() as ddg:
        # Books / purchase (general)
        for t in topics[:4]:
            for r in ddg.text(f"{t} textbook buy", max_results=max_per_kind):
                title, link = r.get("title", "").strip(), r.get("href", "").strip()
                if title and link:
                    results.append(Resource(title=title, type="book", link=link, price=None, provider=None))
        # PDFs (free)
        for t in topics[:4]:
            for r in ddg.text(f"{t} filetype:pdf", max_results=max_per_kind):
                title, link = r.get("title", "").strip(), r.get("href", "").strip()
                if title and link and link.lower().endswith(".pdf"):
                    results.append(Resource(title=title, type="pdf", link=link, price="Free", provider="Open PDF", embed_url=_pdf_embed(link)))
        # Videos (YouTube)
        for t in topics[:4]:
            for r in ddg.videos(f"{t} tutorial site:youtube.com", max_results=max_per_kind):
                title = (r.get("title") or "").strip()
                # some versions return 'href', others 'content' — check both
                link = (r.get("href") or r.get("content") or "").strip()
                if not link:
                    continue
                embed = _youtube_embed(link)
                results.append(Resource(title=title or t, type="video", link=link, price="Free", provider="YouTube", embed_url=embed))
        # Courses (MOOCs)
        for t in topics[:3]:
            for r in ddg.text(f"{t} course MIT Coursera edX", max_results=max_per_kind):
                title, link = r.get("title", "").strip(), r.get("href", "").strip()
                if title and link:
                    results.append(Resource(title=title, type="course", link=link, price=None, provider=None))

    return results


# ---------- Route ----------
@router.post("/suggest", response_model=SuggestResp)
def suggest(req: SuggestReq):
    # 1) Gather/normalize gaps
    llm = OllamaGenerateClient(model="llama3.1")
    topics = req.gaps[:]
    if not topics:
        mined = _mine_gaps_from_attempts(limit=20)
        if mined:
            topics = _condense_topics_with_llm(llm, mined)
    if not topics:
        raise HTTPException(status_code=400, detail="No gaps provided and none inferred from attempts.")

    # 2) Make atomic to-dos
    tasks = _make_tasks_with_llm(llm, topics, req.time_per_day, req.horizon_weeks)

    # 3) Find resources
    resources = _search_resources(topics)

    # 4) Fill cheap pricing hints
    for r in resources:
        if r.type in ("pdf","video","article"):
            r.price = r.price or "Free"
        if r.type == "book" and r.price is None:
            r.price = "Varies"

    return SuggestResp(tasks=tasks, resources=resources)
