# server/services/attempts.py
from __future__ import annotations
import json, sqlite3, os, datetime
from typing import Any, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "store", "siraj.sqlite3")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def _conn():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("""
    CREATE TABLE IF NOT EXISTS quiz_attempts (
      attempt_id   TEXT PRIMARY KEY,
      quiz_id      TEXT NOT NULL,
      doc_id       TEXT NOT NULL,
      score        REAL NOT NULL,
      per_question_json TEXT NOT NULL,
      created_at   TEXT NOT NULL
    );
    """)
    return con

def save_quiz_attempt(attempt_id: str, quiz_id: str, doc_id: str, score: float, per_question: list[dict[str, Any]]) -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT INTO quiz_attempts(attempt_id, quiz_id, doc_id, score, per_question_json, created_at) VALUES (?,?,?,?,?,?)",
            (
                attempt_id,
                quiz_id,
                doc_id,
                float(score),
                json.dumps(per_question, ensure_ascii=False),
                datetime.datetime.utcnow().isoformat() + "Z",
            ),
        )
        con.commit()
    finally:
        con.close()

def get_attempts(limit: int = 20) -> list[Dict[str, Any]]:
    con = _conn()
    try:
        rows = con.execute(
            "SELECT attempt_id, quiz_id, doc_id, score, per_question_json, created_at "
            "FROM quiz_attempts ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        out = []
        for r in rows:
            out.append({
                "attempt_id": r[0],
                "quiz_id": r[1],
                "doc_id": r[2],
                "score": r[3],
                "per_question": json.loads(r[4]),
                "created_at": r[5],
            })
        return out
    finally:
        con.close()
