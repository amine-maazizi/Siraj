# tests/test_embed_ollama.py
import requests
import json
import sys

BASE = "http://localhost:11434"
MODEL = "nomic-embed-text"  # or "mxbai-embed-large"

def post(url, payload):
    r = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=60,
    )
    r.raise_for_status()
    return r.json()

# 1) Check version (optional sanity check)
try:
    v = requests.get(f"{BASE}/api/version", timeout=5).json()
    print("Ollama version:", v)
except Exception as e:
    print("Could not read /api/version:", e)

# 2) /api/embed — single string
data = post(f"{BASE}/api/embed", {"model": MODEL, "input": "Hello world"})
embeds = data.get("embeddings", [])
assert embeds and isinstance(embeds[0], list) and len(embeds[0]) > 0, "No embeddings from /api/embed (single)"
print("/api/embed (single) ok → dim:", len(embeds[0]))

# 3) /api/embed — batch
data = post(f"{BASE}/api/embed", {"model": MODEL, "input": ["Hello world", "Goodbye world"]})
embeds = data.get("embeddings", [])
assert len(embeds) == 2 and all(isinstance(v, list) and len(v) > 0 for v in embeds), "No embeddings from /api/embed (batch)"
print("/api/embed (batch) ok → dims:", [len(v) for v in embeds])

print("✅ All /api/embed tests passed")
