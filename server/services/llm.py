import requests
from fastapi import HTTPException

class OllamaGenerateClient:
    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, temperature: float = 0.2, num_predict: int = 512) -> str:
        try:
            r = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": num_predict},
                },
                timeout=120,
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("response", "").strip()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM generate error: {e}")
