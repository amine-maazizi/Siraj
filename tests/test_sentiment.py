# tests/test_sentiment.py
import requests

BASE_URL = "http://localhost:8000"  # FastAPI server
DOC_ID = "doc_da199418"  # replace with an actual doc_id from /documents

# Sample messages to test all sentiment types
samples = [
    ("This is absolutely wonderful and I love how clear it is!", "positive"),
    ("Can you explain this part more?", "neutral"),
    ("This is frustrating and really hard to understand!", "negative"),
]

def run_test():
    for text, expected in samples:
        payload = {
            "doc_id": DOC_ID,
            "messages": [{"role": "user", "content": text}]
        }
        r = requests.post(f"{BASE_URL}/chat", json=payload)
        print(f"\n--- Testing: {text}")
        if r.status_code != 200:
            print(f"❌ Request failed: {r.status_code} {r.text}")
            continue
        data = r.json()
        print("Answer:", data.get("answer"))
        print("Sentiment:", data.get("sentiment"), "Emoji:", data.get("emoji"))
        if data.get("sentiment") == expected:
            print("✅ Correct sentiment")
        else:
            print(f"⚠️ Expected {expected}, got {data.get('sentiment')}")

if __name__ == "__main__":
    run_test()
