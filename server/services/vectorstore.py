from langchain_chroma import Chroma
from .embedder import OllamaEmbedViaEmbedRoute

def get_vectordb(persist_directory: str, base_url: str, embed_model: str) -> Chroma:
    embed = OllamaEmbedViaEmbedRoute(model=embed_model, base_url=base_url)
    return Chroma(
        collection_name="siraj_docs",
        embedding_function=embed,
        persist_directory=persist_directory,
    )
