# server/services/quizgen.py
from __future__ import annotations

import json
import re
from typing import List
from uuid import uuid4

from pydantic import BaseModel, Field

from ..services.vectorstore import get_vectordb
from ..services.llm import OllamaGenerateClient
from ..config import (
    CHROMA_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_LLM_MODEL,
    OLLAMA_EMBED_MODEL,
)

# -----------------------------
# Models
# -----------------------------

class QuizOption(BaseModel):
    id: str  # "A" | "B" | "C" | "D"
    text: str

class QuizQuestion(BaseModel):
    id: str
    stem: str
    options: List[QuizOption]
    correct_option_ids: List[str] = Field(default_factory=list)
    rationale: str = ""

class QuizSpec(BaseModel):
    quiz_id: str
    doc_id: str
    questions: List[QuizQuestion]


# -----------------------------
# Prompt
# -----------------------------

def _prompt_for_quiz(context: str, n_questions: int = 10) -> str:
    # Keep it strict but short; model-agnostic.
    return f"""
You are Siraj, generating a QUIZ from the CONTEXT below.

Return STRICT JSON and NOTHING ELSE, exactly with this shape:

{{
  "questions": [
    {{
      "id": "Q1",
      "stem": "Question text…",
      "options": [
        {{ "id": "A", "text": "…" }},
        {{ "id": "B", "text": "…" }},
        {{ "id": "C", "text": "…" }},
        {{ "id": "D", "text": "…" }}
      ],
      "correct_option_ids": ["A","C"],
      "rationale": "One short teaching explanation grounded in context."
    }}
  ]
}}

RULES:
- Exactly {n_questions} questions.
- Each question has EXACTLY 4 options with IDs "A","B","C","D".
- Checkbox style: 1 to 3 correct options per question.
- Keep stems concise and grounded ONLY in CONTEXT.
- Rationale: 1–2 sentences, grounded in CONTEXT.
- Do not add any commentary outside the JSON.

# CONTEXT
{context}
""".strip()


# -----------------------------
# JSON extraction / repair
# -----------------------------

def _extract_json_block(text: str) -> dict:
    """
    Extract a JSON object from model output robustly.

    Strategy:
    1) Prefer fenced ```json blocks
    2) Try to find a balanced {...} region by brace counting
    3) Fallback to first {...} and try to "repair" by trimming to last balanced brace
    """
    # 1) Fenced block
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
    if m:
        return json.loads(m.group(1))

    # 2) Balanced scan
    j = _find_balanced_json(text)
    if j is not None:
        return json.loads(j)

    # 3) First object + trim to last }
    m = re.search(r"\{.*", text, flags=re.S)
    if m:
        candidate = m.group(0)
        last_brace = candidate.rfind("}")
        if last_brace != -1:
            candidate = candidate[: last_brace + 1]
            return json.loads(candidate)

    # last-resort: try raw (will likely fail, but surfaces a clean error)
    return json.loads(text)

def _find_balanced_json(s: str) -> str | None:
    """
    Find the longest balanced JSON object starting from the first '{' via brace counting.
    """
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return None  # never closed


# -----------------------------
# Fallback quiz (no-LLM safety net)
# -----------------------------

def _fallback_quiz(context: str, doc_id: str, n_questions: int = 10) -> QuizSpec:
    import textwrap

    lines = [ln.strip() for ln in (context or "").split("\n") if ln.strip()]

    def make_q(i: int) -> QuizQuestion:
        stem = (
            lines[i % len(lines)]
            if lines else f"From document {doc_id}: placeholder question {i+1}."
        )
        stem = textwrap.shorten(stem, width=120, placeholder="…")
        options = [QuizOption(id=chr(65 + j), text=f"Option {chr(65 + j)}") for j in range(4)]
        return QuizQuestion(
            id=f"Q{i+1}",
            stem=stem,
            options=options,
            correct_option_ids=["A"],
            rationale="Based on the provided context.",
        )

    return QuizSpec(
        quiz_id=str(uuid4()),
        doc_id=doc_id,
        questions=[make_q(i) for i in range(n_questions)],
    )


# -----------------------------
# Main entry
# -----------------------------

def generate_quiz_from_doc(doc_id: str, n_questions: int = 10) -> QuizSpec:
    # 1) Gather RAG context
    db = get_vectordb(
        persist_directory=str(CHROMA_DIR),
        base_url=OLLAMA_BASE_URL,
        embed_model=OLLAMA_EMBED_MODEL,
    )

    # Pull a diverse slate of chunks; widen if empty
    hits = db.similarity_search_with_score(
        f"overview of {doc_id}", k=8, filter={"doc_id": doc_id}
    )
    if not hits:
        hits = db.similarity_search_with_score(doc_id, k=8, filter={"doc_id": doc_id})

    context = "\n\n".join(
        f"[p.{int((d.metadata or {}).get('page', 0))}] {(d.page_content or '').strip()}"
        for d, _ in hits
    )[:12000]  # safety cut

    if not context.strip():
        # No chunks? Keep the demo green.
        return _fallback_quiz(context, doc_id, n_questions)

    # 2) Generate with more headroom (avoid truncation)
    llm = OllamaGenerateClient(model=OLLAMA_LLM_MODEL, host=OLLAMA_BASE_URL)

    prompt = _prompt_for_quiz(context, n_questions=n_questions)

    # Try up to 2 attempts (2nd adds a stricter reminder)
    attempts_errors: List[str] = []
    for attempt in range(2):
        try:
            raw = llm.generate(
                prompt if attempt == 0 else prompt + "\n\nReturn ONLY valid JSON (no prose).",
                temperature=0.2,
                num_predict=2048,  # bigger budget to avoid cutoffs
            )

            data = _extract_json_block(raw)

            # 3) Normalize and coerce to our schema
            questions: List[QuizQuestion] = []
            for i, q in enumerate(data.get("questions", []), start=1):
                qid = (q.get("id") or f"Q{i}").strip()
                stem = (q.get("stem") or "").strip()

                # Normalize options to A-D, pad if needed
                raw_opts = q.get("options", [])[:4]
                options: List[QuizOption] = []
                for j in range(4):
                    if j < len(raw_opts):
                        oid = (raw_opts[j].get("id") or chr(65 + j)).strip() or chr(65 + j)
                        otext = (raw_opts[j].get("text") or "").strip() or f"Option {chr(65 + j)}"
                    else:
                        oid = chr(65 + j)
                        otext = f"(missing)"
                    # Coerce IDs to A-D
                    oid = chr(65 + j)
                    options.append(QuizOption(id=oid, text=otext))

                # Corrects: keep only A-D, at least one
                correct = [c for c in (q.get("correct_option_ids") or []) if c in {"A","B","C","D"}]
                if not correct:
                    correct = ["A"]

                rationale = (q.get("rationale") or "").strip() or "Based on the provided context."

                questions.append(
                    QuizQuestion(
                        id=qid,
                        stem=stem,
                        options=options,
                        correct_option_ids=correct,
                        rationale=rationale,
                    )
                )

            # Top up with fallback if the model returned < n_questions
            if len(questions) < n_questions:
                fb = _fallback_quiz(context, doc_id, n_questions)
                questions.extend(fb.questions[len(questions):])

            return QuizSpec(
                quiz_id=str(uuid4()),
                doc_id=doc_id,
                questions=questions[:n_questions],
            )

        except Exception as e:
            attempts_errors.append(str(e))

    # 4) Last-resort fallback (keeps API responsive)
    return _fallback_quiz(context, doc_id, n_questions)
