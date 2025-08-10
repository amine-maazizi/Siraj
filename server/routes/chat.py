# server/routes/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any
from ..deps import get_vectordb
from ..services.llm import OllamaGenerateClient
from ..services.sentiment import classify_sentiment, sentiment_emoji
from ..config import OLLAMA_BASE_URL, OLLAMA_LLM_MODEL

router = APIRouter(prefix="/chat", tags=["chat"])

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    doc_id: str = Field(..., description="Document ID to ground RAG on")
    messages: List[Message] = Field(..., description="Full chat history (minimal OK)")

class Citation(BaseModel):
    page: int
    snippet: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    sentiment: Literal["positive", "neutral", "negative"] = "neutral"
    emoji: str = "🙂"

def _build_prompt(context_blocks: List[Dict[str, Any]], history: List[Message], mood: str) -> str:
    context_text = "\n\n".join(
        f"[p.{m.get('page', '?')}] {m.get('text','')}" for m in context_blocks
    )
    history_text = "\n".join(f"{m.role.upper()}: {m.content}" for m in history[-6:])  # small window
    tone_line = {
        "positive": "Be concise and encouraging.",
        "neutral":  "Be clear and direct.",
        "negative": "Be extra gentle, simplify concepts, and offer a short analogy.",
    }[mood]

    return f"""You are Siraj, a helpful tutor. Use ONLY the context to answer.
If something is unknown or outside the context, say you don't know.

{tone_line}

# CONTEXT
{context_text}

# CHAT (latest last)
{history_text}

ASSISTANT:"""

@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages is empty")

    # 1) Sentiment on latest user message
    last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
    user_text = last_user.content if last_user else ""
    mood, confidence = classify_sentiment(user_text)
    emoji = sentiment_emoji(mood)

    # 2) Retrieve context from Chroma
    db = get_vectordb()
    query_text = user_text or req.messages[-1].content
    results = db.similarity_search_with_score(query_text, k=4, filter={"doc_id": req.doc_id})

    context_blocks = []
    citations: List[Citation] = []
    for doc, score in results:
        meta = doc.metadata or {}
        page = int(meta.get("page", 0))
        text = (doc.page_content or "").strip().replace("\n", " ")
        # keep tidy snippets
        snippet = (text[:300] + "…") if len(text) > 320 else text
        context_blocks.append({"page": page, "text": text})
        citations.append(Citation(page=page, snippet=snippet))

    # 3) Generate with tone adapted to sentiment
    llm = OllamaGenerateClient(model=OLLAMA_LLM_MODEL, host=OLLAMA_BASE_URL)
    prompt = _build_prompt(context_blocks, req.messages, mood)
    raw_answer = llm.generate(prompt, temperature=0.2, num_predict=512)

    # 4) Add small empathetic lead-in emoji (non-intrusive)
    friendly_answer = f"{emoji} {raw_answer}".strip()

    return ChatResponse(
        answer=friendly_answer,
        citations=citations,
        sentiment=mood,
        emoji=emoji,
    )
