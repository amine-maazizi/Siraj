# server/services/llm.py
from fastapi import HTTPException
from ollama import Client

class OllamaGenerateClient:
    def __init__(self, model: str, host: str | None = None):
        self.model = model
        # If host is None, Client() uses OLLAMA_HOST env or the default localhost:11434
        self.client = Client(host=host) if host else Client()

    def generate(self, prompt: str, temperature: float = 0.2, num_predict: int = 512) -> str:
        try:
            result = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": temperature,
                    "num_predict": num_predict,
                },
                stream=False,
            )
            return (result.get("response") or "").strip()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM generate error: {e}")
