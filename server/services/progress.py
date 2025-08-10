# server/services/progress.py
from __future__ import annotations
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

DB_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "store" / "sqlite.db",
    Path(__file__).resolve().parent.parent / "store" / "siraj.sqlite3",
]


# --- add near the top (after imports) ---
def _ensure_min_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Create only what /progress reads; harmless if already present.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY,
            title TEXT,
            path TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quizzes(
            id INTEGER PRIMARY KEY,
            doc_id INTEGER,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts(
            id INTEGER PRIMARY KEY,
            quiz_id INTEGER,
            started_at TEXT,
            finished_at TEXT,
            score REAL,
            feedback_json TEXT
        )
    """)
    # Optional: gaps table (used if present)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gaps(
            topic TEXT,
            note TEXT
        )
    """)
    conn.commit()


def _db_path() -> str:
    for p in DB_CANDIDATES:
        if p.exists():
            return str(p)
    # Fallback: create store/sqlite.db if missing
    fallback = DB_CANDIDATES[0]
    fallback.parent.mkdir(parents=True, exist_ok=True)
    return str(fallback)

def _q(conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    cur = conn.execute(sql, params)
    return cur.fetchall()

def _get_avg_score(conn: sqlite3.Connection) -> float:
    rows = _q(conn, "SELECT AVG(score) AS avg_score FROM quiz_attempts")
    val = rows[0]["avg_score"]
    return float(val) if val is not None else 0.0

def _get_docs_count(conn: sqlite3.Connection) -> int:
    rows = _q(conn, "SELECT COUNT(*) AS n FROM documents")
    return int(rows[0]["n"]) if rows else 0

def _get_quiz_count(conn: sqlite3.Connection) -> int:
    rows = _q(conn, "SELECT COUNT(*) AS n FROM quiz_attempts")
    return int(rows[0]["n"]) if rows else 0

def _get_history(conn: sqlite3.Connection, limit: int = 50) -> List[Dict[str, Any]]:
    ts_col = _pick_ts_col(conn)  # e.g., "created_at" if "finished_at" is missing

    # Build SQL string using the chosen timestamp column
    sql = f"""
    SELECT qa.id AS attempt_id,
           qa.{ts_col} AS ts_raw,
           qa.score AS score,
           q.id AS quiz_id,
           d.title AS doc_title
    FROM quiz_attempts qa
    LEFT JOIN quizzes q ON q.id = qa.quiz_id
    LEFT JOIN documents d ON d.id = q.doc_id
    WHERE qa.{ts_col} IS NOT NULL
    ORDER BY qa.{ts_col} ASC
    LIMIT ?
    """

    rows = _q(conn, sql, (limit,))
    hist: List[Dict[str, Any]] = []
    for r in rows:
        dt = r["ts_raw"]
        # Accept numeric timestamps or ISO strings
        if isinstance(dt, (int, float)):
            date_str = datetime.fromtimestamp(dt).strftime("%Y-%m-%d")
        else:
            try:
                date_str = datetime.fromisoformat(str(dt)).strftime("%Y-%m-%d")
            except Exception:
                date_str = str(dt)
        hist.append({
            "date": date_str,
            "score": float(r["score"] or 0),
            "doc": r["doc_title"] or "Untitled",
            "attempt_id": int(r["attempt_id"]),
        })
    return hist


def _get_gaps(conn: sqlite3.Connection, limit: int = 12) -> List[Dict[str, Any]]:
    """
    Best-effort gap extraction:
    - If review/gaps table exists → use it.
    - Else try from quiz_attempts.feedback_json fields.
    """
    try:
        rows = _q(conn, "SELECT topic, note FROM gaps ORDER BY rowid DESC LIMIT ?", (limit,))
        return [{"topic": r["topic"], "note": r["note"]} for r in rows]
    except Exception:
        pass

    # Fallback: parse feedback_json (if present) for weak topics keywords
    try:
        rows = _q(conn, "SELECT feedback_json FROM quiz_attempts ORDER BY finished_at DESC LIMIT 50")
        import json
        topics: Dict[str, str] = {}
        for r in rows:
            raw = r["feedback_json"]
            if not raw:
                continue
            try:
                fb = json.loads(raw)
            except Exception:
                continue
            # look for common shapes: {"weak_topics":[{"topic":..., "note":...}]}
            if isinstance(fb, dict) and "weak_topics" in fb and isinstance(fb["weak_topics"], list):
                for it in fb["weak_topics"]:
                    t = str(it.get("topic", "")).strip()
                    n = str(it.get("note", "")).strip()
                    if t and t not in topics:
                        topics[t] = n or "Needs revision"
            # or per_question rationales → extract a key topic if provided
            if isinstance(fb, dict) and "per_question" in fb and isinstance(fb["per_question"], list):
                for pq in fb["per_question"]:
                    t = str(pq.get("topic", "")).strip()
                    if t and t not in topics:
                        topics[t] = str(pq.get("rationale", "Needs revision"))[:160]
        out = [{"topic": k, "note": v} for k, v in list(topics.items())[:limit]]
        return out
    except Exception:
        return []

def _compute_streak(hist: List[Dict[str, Any]]) -> int:
    """
    Simple daily streak: consecutive days with at least one attempt, ending today.
    """
    if not hist:
        return 0
    days = {h["date"] for h in hist if h.get("date")}
    today = datetime.now().date()
    streak = 0
    d = today
    while d.strftime("%Y-%m-%d") in days:
        streak += 1
        d = d - timedelta(days=1)
    return streak

def _trend(hist: List[Dict[str, Any]], window: int = 5) -> float:
    """Return delta between last score and average of previous window (positive = improving)."""
    if not hist:
        return 0.0
    scores = [h["score"] for h in hist if isinstance(h.get("score"), (int, float))]
    if len(scores) < 2:
        return 0.0
    last = scores[-1]
    prev = scores[-(window+1):-1] if len(scores) > window else scores[:-1]
    if not prev:
        return 0.0
    base = sum(prev) / len(prev)
    return last - base

def _review_text(totals: Dict[str, Any], hist: List[Dict[str, Any]], gaps: List[Dict[str, Any]]) -> str:
    docs = totals["docs"]
    quizzes = totals["quizzes"]
    avg_score = totals["avgScore"]
    streak = totals.get("streak", 0)
    delta = totals.get("trendDelta", 0.0)

    last_label = hist[-1]["date"] if hist else "—"
    last_score = hist[-1]["score"] if hist else 0
    weak_blurb = ", ".join([g["topic"] for g in gaps[:3]]) if gaps else "no recurring gaps"

    direction = "up" if delta >= 0 else "down"
    delta_abs = abs(delta)

    return (
        f"As of {last_label}, you’ve studied {docs} document(s) and completed {quizzes} quiz attempt(s). "
        f"Average score sits at {avg_score:.0f}%, with a current streak of {streak} day(s). "
        f"Your last score was {last_score:.0f}%, trending {direction} by {delta_abs:.1f} points versus your recent baseline. "
        f"Weak spots to revisit: {weak_blurb}. Keep the loop tight: quick review → short quiz → iterate."
    )

def get_progress() -> Dict[str, Any]:
    conn = sqlite3.connect(_db_path())
    try:
        _ensure_min_schema(conn)
        totals = {
            "docs": _get_docs_count(conn),
            "quizzes": _get_quiz_count(conn),
            "avgScore": round(_get_avg_score(conn) or 0.0, 2),
        }
        history = _get_history(conn, limit=120)
        totals["streak"] = _compute_streak(history)
        totals["trendDelta"] = round(_trend(history, window=5), 2)
        gaps = _get_gaps(conn, limit=12)
        review = _review_text(totals, history, gaps)
        # Minimal skills placeholder: infer simple buckets from average score
        skills = [
            {"name": "Foundations", "level": min(100, max(0, int(totals["avgScore"])))},
        ]
        return {
            "totals": totals,
            "history": history,
            "skills": skills,
            "gaps": gaps,
            "review": review,
        }
    finally:
        conn.close()

def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())

def _pick_ts_col(conn: sqlite3.Connection) -> str:
    # Prefer these, in order; fall back to any available
    candidates = ["finished_at", "completed_at", "ended_at", "created_at", "updated_at", "started_at"]
    for c in candidates:
        if _column_exists(conn, "quiz_attempts", c):
            return c
    # absolute fallback: create a synthetic created_at if truly nothing exists
    # but in practice quiz_attempts will have at least one of above
    return "created_at"
