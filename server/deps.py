from server.services.vectorstore import get_vectordb
from server.services.embedder import OllamaEmbedViaEmbedRoute
from server.config import CHROMA_DIR, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL

# Create embedding function once
embedding_fn = OllamaEmbedViaEmbedRoute(
    model=OLLAMA_EMBED_MODEL,
    base_url=OLLAMA_BASE_URL
)

# Create persistent vectordb instance once
vectordb = get_vectordb(
    persist_directory=str(CHROMA_DIR),
    base_url=OLLAMA_BASE_URL,
    embed_model=OLLAMA_EMBED_MODEL
)
