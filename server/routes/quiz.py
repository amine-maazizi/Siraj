from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sqlite3
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


from ..services.quizgen import generate_quiz_from_doc
from ..services import attempts as attempt_store
import uuid

# ---- SQLite helpers ---------------------------------------------------------

def _db_path() -> Path:
    # Prefer config if you have it; otherwise default to server/store/sqlite.db
    try:
        from ..config import SQLITE_DB  # type: ignore
        if SQLITE_DB:
            return Path(SQLITE_DB)
    except Exception:
        pass
    return Path(__file__).resolve().parents[1] / "store" / "sqlite.db"


def _connect():
    dbp = _db_path()
    dbp.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(dbp)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables():
    with _connect() as con:
        cur = con.cursor()
        # quizzes table keeps the generated spec so we can grade later
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS quizzes (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                spec_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        # attempts table stores performance + full feedback
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                score REAL NOT NULL,
                answers_json TEXT NOT NULL,
                feedback_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        con.commit()


# ---- Schemas (aligned to your frontend types) -------------------------------

class QuizOption(BaseModel):
    id: str
    text: str


class QuizQuestion(BaseModel):
    id: str
    stem: str
    options: List[QuizOption]
    multi: bool = True  # checkbox


class GenerateQuizRequest(BaseModel):
    doc_id: str
    n_questions: int = Field(default=10, ge=1, le=20)
    type: str = "checkbox"  # kept for compatibility


class GenerateQuizResponse(BaseModel):
    quiz_id: str
    doc_id: str
    questions: List[QuizQuestion]


class GradeAnswerItem(BaseModel):
    question_id: str
    option_ids: List[str]


class GradeRequest(BaseModel):
    quiz_id: str
    answers: List[GradeAnswerItem]


class GradeOptionResult(BaseModel):
    id: str
    text: str
    selected: bool
    correct: bool


class GradePerQuestion(BaseModel):
    id: str
    correct_option_ids: List[str]
    rationale: str
    options: List[GradeOptionResult]


class GradeResponse(BaseModel):
    score: float
    per_question: List[GradePerQuestion]


# ---- Router -----------------------------------------------------------------

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.post("/generate", response_model=GenerateQuizResponse)
def generate(req: GenerateQuizRequest):
    """
    Generates a quiz *and* persists the quiz spec into SQLite (quizzes table).
    """
    _ensure_tables()

    try:
        spec = generate_quiz_from_doc(req.doc_id, n_questions=req.n_questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generate failed: {e}")

    # Persist spec JSON so the grader can retrieve it deterministically
    with _connect() as con:
        con.execute(
            "INSERT OR REPLACE INTO quizzes (id, doc_id, spec_json, created_at) VALUES (?, ?, ?, ?)",
            (
                spec.quiz_id,
                spec.doc_id,
                json.dumps(spec.dict(), ensure_ascii=False),
                datetime.utcnow().isoformat(),
            ),
        )
        con.commit()

    # Map to frontend shape (multi: true for checkbox)
    out_questions = [
        QuizQuestion(
            id=q.id,
            stem=q.stem,
            options=[QuizOption(id=o.id, text=o.text) for o in q.options],
            multi=True,
        )
        for q in spec.questions
    ]

    return GenerateQuizResponse(quiz_id=spec.quiz_id, doc_id=spec.doc_id, questions=out_questions)


@router.post("/grade", response_model=GradeResponse)
def grade(req: GradeRequest):
    """
    Grades a submission against the stored quiz spec.
    Stores the attempt & feedback in SQLite (quiz_attempts table).
    """
    _ensure_tables()

    # 1) Fetch quiz spec
    with _connect() as con:
        row = con.execute("SELECT spec_json FROM quizzes WHERE id = ?", (req.quiz_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Quiz not found.")
        spec = json.loads(row["spec_json"])

    # 2) Build lookup maps
    questions: List[Dict[str, Any]] = spec["questions"]
    q_by_id: Dict[str, Dict[str, Any]] = {q["id"]: q for q in questions}

    # Normalize user's answers to set per question
    answers_map: Dict[str, List[str]] = {a.question_id: [x.upper() for x in a.option_ids] for a in req.answers}

    per_q_results: List[GradePerQuestion] = []
    total_correct = 0

    for q in questions:
        qid = q["id"]
        opts = q["options"]  # [{'id': 'A', 'text': '...'}, ...]
        # LLM's declared correct answers in spec
        correct_ids = [c.upper() for c in q.get("correct_option_ids", []) if c.upper() in {"A", "B", "C", "D"}]
        if not correct_ids:
            # in case model forgot, make it at least one to avoid 0/0 edge cases
            correct_ids = ["A"]

        # User's selected option ids (uppercased)
        selected_ids = set(answers_map.get(qid, []))

        # exact-match grading on the set of correct options
        is_correct = selected_ids == set(correct_ids)
        if is_correct:
            total_correct += 1

        # Build option-level results
        option_results: List[GradeOptionResult] = []
        for o in opts:
            oid = o["id"].upper()
            option_results.append(
                GradeOptionResult(
                    id=oid,
                    text=o["text"],
                    selected=oid in selected_ids,
                    correct=oid in correct_ids,
                )
            )

        per_q_results.append(
            GradePerQuestion(
                id=qid,
                correct_option_ids=correct_ids,
                rationale=q.get("rationale", "") or "Grounded in the provided context.",
                options=option_results,
            )
        )
    
    # Calculate score after processing all questions
    score = round((total_correct / max(1, len(questions))) * 100.0, 1)
    
    attempt_id = f"{req.quiz_id}:{uuid.uuid4()}"
    per_question_for_suggest = []
    for r in per_q_results:
        per_question_for_suggest.append({
            "id": r.id,
            # use the question stem so /suggest can LLM-condense topics later
            "question": q_by_id[r.id]["stem"],
            # mark correctness; miner can focus on wrong ones
            "correct": set([o.id for o in r.options if o.correct]) == set([o.id for o in r.options if o.selected]),
            # optional: stash rationale for extra signal
            "rationale": r.rationale,
            # if you ever add topic/tag in your generator, include here:
            # "topic": q_by_id[r.id].get("topic")
        })

    attempt_store.save_quiz_attempt(
        attempt_id=attempt_id,
        quiz_id=req.quiz_id,
        doc_id=spec["doc_id"],
        score=score,
        per_question=per_question_for_suggest
    )

    # 3) Persist attempt
    attempt_payload = {
        "answers": [{"question_id": a.question_id, "option_ids": a.option_ids} for a in req.answers]
    }
    feedback_payload = {
        "score": score,
        "per_question": [r.dict() for r in per_q_results],
    }

    with _connect() as con:
        con.execute(
            """
            INSERT INTO quiz_attempts (quiz_id, doc_id, score, answers_json, feedback_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                req.quiz_id,
                spec["doc_id"],
                float(score),
                json.dumps(attempt_payload, ensure_ascii=False),
                json.dumps(feedback_payload, ensure_ascii=False),
                datetime.utcnow().isoformat(),
            ),
        )
        con.commit()

    return GradeResponse(score=score, per_question=per_q_results)


# Optional: expose attempts for dashboards/history
class AttemptDTO(BaseModel):
    id: int
    quiz_id: str
    doc_id: str
    score: float
    created_at: str


@router.get("/attempts", response_model=List[AttemptDTO])
def list_attempts(doc_id: Optional[str] = None, limit: int = 25):
    _ensure_tables()
    with _connect() as con:
        if doc_id:
            rows = con.execute(
                """
                SELECT id, quiz_id, doc_id, score, created_at
                FROM quiz_attempts
                WHERE doc_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (doc_id, limit),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT id, quiz_id, doc_id, score, created_at
                FROM quiz_attempts
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return [AttemptDTO(**dict(r)) for r in rows]
