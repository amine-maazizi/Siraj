# server/services/vectorstore.py
from langchain_chroma import Chroma
import chromadb
from .embedder import OllamaEmbedViaEmbedRoute

_client = None
def _get_client(persist_directory: str) -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=persist_directory)
    return _client

def get_vectordb(persist_directory: str, base_url: str, embed_model: str) -> Chroma:
    embed = OllamaEmbedViaEmbedRoute(model=embed_model, base_url=base_url)
    return Chroma(
        collection_name="siraj_docs",          # must match everywhere
        embedding_function=embed,
        persist_directory=persist_directory,   # must match CHROMA_DIR
    )
