from typing import List
import requests
from fastapi import HTTPException

class OllamaEmbedViaEmbedRoute:
    """
    Minimal embeddings client compatible with LangChain's Embeddings interface.
    Uses Ollama /api/embed directly.
    """
    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _post_embed(self, inputs: List[str]) -> List[List[float]]:
        try:
            r = requests.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model, "input": inputs},
                timeout=60,
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
            embeddings = data.get("embeddings", [])
            if not embeddings or not isinstance(embeddings, list):
                raise RuntimeError("No embeddings returned from /api/embed")
            return embeddings
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Embedding error: {e}")

    # LangChain interface
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self._post_embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._post_embed([text])[0]
