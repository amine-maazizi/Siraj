# server/config.py
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Optional

# -------- Rooted paths / defaults --------
PROJECTS_DIR = Path(os.getenv("SIRAJ_PROJECTS_DIR", "./SirajProjects")).resolve()
DEFAULT_PROJECT = os.getenv("SIRAJ_DEFAULT_PROJECT", "ExampleProject")

# Where the server stores current activation (written by /projects endpoints)
ACTIVE_PATHS_FILE = Path(os.getenv("SIRAJ_ACTIVE_PATHS", "server/store/active_paths.json")).resolve()

# Fallback (used when no active project set)
FALLBACK_CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "server/store/chroma")).resolve()

# -------- LLM / Embedding --------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1")

# -------- Summarize tuning --------
SUMMARIZE_TOPK = int(os.getenv("SUMMARIZE_TOPK", "200"))
SUMMARIZE_MAX_MAP_CHUNKS = int(os.getenv("SUMMARIZE_MAX_MAP_CHUNKS", "60"))

# -------- Helpers --------
def _read_active_paths() -> Optional[dict]:
    """Return active_paths.json if present, else None."""
    try:
        if ACTIVE_PATHS_FILE.exists():
            return json.loads(ACTIVE_PATHS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None

def resolve_chroma_dir() -> Path:
    """
    Returns the Chroma persist directory for the active project if set,
    otherwise falls back to global CHROMA_DIR (FALLBACK_CHROMA_DIR).
    """
    active = _read_active_paths()
    if active and "chroma_dir" in active:
        return Path(active["chroma_dir"]).resolve()
    return FALLBACK_CHROMA_DIR

def ensure_project_scaffold(project_id: str | None = None):
    """
    Minimal PoC scaffold creation. Creates resources/ and media/ for a project,
    and ensures a chroma dir exists for fallback or active project.
    """
    pid = project_id or DEFAULT_PROJECT
    proj_root = (PROJECTS_DIR / pid).resolve()
    (proj_root / "resources").mkdir(parents=True, exist_ok=True)
    (proj_root / "media").mkdir(parents=True, exist_ok=True)

    # Ensure fallback chroma (useful in dev if no project switching yet)
    FALLBACK_CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Keep PoC behavior: ensure default project dirs exist once at import.
ensure_project_scaffold(DEFAULT_PROJECT)

CHROMA_DIR = FALLBACK_CHROMA_DIR
