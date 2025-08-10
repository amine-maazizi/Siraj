# server/deps.py
from __future__ import annotations
from functools import lru_cache
from typing import Optional

from server.services.vectorstore import get_vectordb as _make_vectordb
from server.services.embedder import OllamaEmbedViaEmbedRoute
from server.config import (
    resolve_chroma_dir,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
)

# ---------- Embeddings ----------
@lru_cache(maxsize=4)
def get_embedding_fn(
    model: str = OLLAMA_EMBED_MODEL,
    base_url: str = OLLAMA_BASE_URL,
) -> OllamaEmbedViaEmbedRoute:
    """
    Lazily create (and cache) the embedding function by model+base_url.
    """
    return OllamaEmbedViaEmbedRoute(model=model, base_url=base_url)

# ---------- Vector DB (project-aware) ----------
@lru_cache(maxsize=8)
def _vectordb_for_dir(
    persist_directory: str,
    base_url: str = OLLAMA_BASE_URL,
    embed_model: str = OLLAMA_EMBED_MODEL,
):
    """
    Internal cache keyed by the Chroma persist directory (plus embed settings).
    """
    return _make_vectordb(
        persist_directory=persist_directory,
        base_url=base_url,
        embed_model=embed_model,
    )

def get_vectordb():
    """
    Public accessor that looks up the CURRENT active project's chroma dir
    every time it is called, and returns a cached instance for that dir.
    """
    chroma_dir = str(resolve_chroma_dir())
    # Using the cached factory by directory keeps switching fast without leaks.
    return _vectordb_for_dir(
        persist_directory=chroma_dir,
        base_url=OLLAMA_BASE_URL,
        embed_model=OLLAMA_EMBED_MODEL,
    )
