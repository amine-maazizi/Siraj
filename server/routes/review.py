from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/review", tags=["review"])

# --- SQLite helpers ----------------------------------------------------------

def _db_path() -> str:
    # Align with server/routes/quiz.py default path
    return "server/store/sqlite.db"

def _connect():
    con = sqlite3.connect(_db_path())
    con.row_factory = sqlite3.Row
    return con

def _ensure_tables():
    with _connect() as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
              id TEXT PRIMARY KEY,
              doc_id TEXT NOT NULL,
              spec_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              quiz_id TEXT NOT NULL,
              doc_id TEXT NOT NULL,
              score REAL NOT NULL,
              answers_json TEXT NOT NULL,
              feedback_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
        """)
        con.commit()

# --- Schemas -----------------------------------------------------------------

class ReviewWrongItem(BaseModel):
    question_id: str
    stem: str
    selected_texts: List[str] = Field(default_factory=list)
    correct_texts: List[str] = Field(default_factory=list)
    explanation: str
    related_pages: List[int] = Field(default_factory=list)  # stays empty unless you later add citations

class ReviewDoc(BaseModel):
    doc_id: str
    title: str
    attempt_id: int
    score: float
    taken_at: str
    wrong: List[ReviewWrongItem]

class ReviewResponse(BaseModel):
    reviews: List[ReviewDoc]

# --- Core --------------------------------------------------------------------

def _latest_attempt_per_doc() -> List[sqlite3.Row]:
    """
    Returns rows of the latest attempt for each doc_id, joined with the quiz spec.
    Only depends on quizzes + quiz_attempts tables.
    """
    _ensure_tables()
    q = """
    SELECT
      qa.id               AS attempt_id,
      qa.quiz_id          AS quiz_id,
      qa.doc_id           AS doc_id,
      qa.score            AS score,
      qa.feedback_json    AS feedback_json,
      qa.created_at       AS created_at,
      qz.spec_json        AS spec_json
    FROM quiz_attempts qa
    JOIN quizzes qz ON qz.id = qa.quiz_id
    JOIN (
      SELECT qz.doc_id AS doc_id, MAX(qa.created_at) AS max_created
      FROM quiz_attempts qa
      JOIN quizzes qz ON qz.id = qa.quiz_id
      GROUP BY qz.doc_id
    ) mx ON mx.doc_id = qz.doc_id AND mx.max_created = qa.created_at
    ORDER BY qa.created_at DESC;
    """
    with _connect() as con:
        return con.execute(q).fetchall()

def _parse_spec(spec_json: str) -> Dict[str, Dict[str, Any]]:
    """
    Build question map: qid -> { stem, options: [{id,text}, ...] }
    """
    try:
        spec = json.loads(spec_json or "{}")
    except Exception:
        spec = {}
    out: Dict[str, Dict[str, Any]] = {}
    for q in spec.get("questions", []) or []:
        qid = str(q.get("id"))
        out[qid] = {
            "stem": q.get("stem", "") or "",
            "options": q.get("options", []) or [],
        }
    return out

def _safe_json(s: Optional[str]) -> Any:
    try:
        return json.loads(s) if s else None
    except Exception:
        return None

def _build_wrong_items(spec_map: Dict[str, Dict[str, Any]], feedback: Dict[str, Any]) -> List[ReviewWrongItem]:
    """Use saved feedback_json from /quiz/grade to detect wrong Qs and explain them."""
    wrong: List[ReviewWrongItem] = []
    per_q = feedback.get("per_question", []) or []
    for item in per_q:
        qid = str(item.get("id"))
        spec = spec_map.get(qid, {"stem": "", "options": []})
        opts = spec.get("options", [])

        # From grader we stored: options: [{id,text,selected,correct}], plus correct_option_ids and rationale.
        options_fb = item.get("options", []) or []
        selected_texts = [o.get("text", "") for o in options_fb if o.get("selected")]
        correct_texts  = [o.get("text", "") for o in options_fb if o.get("correct")]

        # Decide correctness by comparing sets of selected vs correct IDs
        sel_ids = {o.get("id") for o in options_fb if o.get("selected")}
        cor_ids = {o.get("id") for o in options_fb if o.get("correct")}
        is_correct = sel_ids == cor_ids

        if not is_correct:
            wrong.append(ReviewWrongItem(
                question_id=qid,
                stem=spec.get("stem", ""),
                selected_texts=selected_texts,
                correct_texts=correct_texts,
                explanation=item.get("rationale") or "Review this concept in the source PDF.",
                related_pages=[],  # fill later if you add citations with page numbers
            ))
    return wrong

# --- Route -------------------------------------------------------------------

@router.get("", response_model=ReviewResponse)
def get_review() -> ReviewResponse:
    """
    For each document that has quiz attempts, return the latest attempt's wrong questions.
    """
    rows = _latest_attempt_per_doc()
    reviews: List[ReviewDoc] = []

    for r in rows:
        spec_map = _parse_spec(r["spec_json"])
        feedback = _safe_json(r["feedback_json"]) or {}

        wrong_items = _build_wrong_items(spec_map, feedback)
        if not wrong_items:
            # If the latest attempt for this doc was perfect, skip it.
            continue

        reviews.append(ReviewDoc(
            doc_id=str(r["doc_id"]),
            title=str(r["doc_id"]),       # we don't have a documents table; display doc_id as title
            attempt_id=int(r["attempt_id"]),
            score=float(r["score"]),
            taken_at=str(r["created_at"]),
            wrong=wrong_items,
        ))

    return ReviewResponse(reviews=reviews)
