# tests/test_summarize.py
import requests
import json

API_BASE = "http://localhost:8000"  # adjust if running remotely
DOC_ID = "doc_6fea5504"

def test_summarize():
    url = f"{API_BASE}/summarize"
    payload = {"doc_id": DOC_ID}
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return

    print(f"Status: {resp.status_code}")
    if resp.ok:
        try:
            data = resp.json()
        except json.JSONDecodeError:
            print("❌ Could not decode JSON.")
            print(resp.text)
            return

        print(json.dumps(data, indent=2))
    else:
        print("❌ Error response:")
        print(resp.text)

if __name__ == "__main__":
    test_summarize()
