import os
from pathlib import Path

# Rooted paths
PROJECTS_DIR = Path(os.getenv("SIRAJ_PROJECTS_DIR", "./SirajProjects"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "server/store/chroma"))
DEFAULT_PROJECT = os.getenv("SIRAJ_DEFAULT_PROJECT", "ExampleProject")

# LLM/Embedding
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1")

# Summarize tuning
SUMMARIZE_TOPK = int(os.getenv("SUMMARIZE_TOPK", "200"))
SUMMARIZE_MAX_MAP_CHUNKS = int(os.getenv("SUMMARIZE_MAX_MAP_CHUNKS", "60"))

# Ensure required dirs exist (PoC)
(PROJECTS_DIR / DEFAULT_PROJECT / "resources").mkdir(parents=True, exist_ok=True)
(PROJECTS_DIR / DEFAULT_PROJECT / "media").mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
