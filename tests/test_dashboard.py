# test_dashboard.py
import requests

API_BASE = "http://localhost:8000"  # FastAPI server must be running
ENDPOINT = f"{API_BASE}/progress"

def main():
    try:
        print(f"Calling GET {ENDPOINT} ...")
        resp = requests.get(ENDPOINT, timeout=10)
        print(f"Status: {resp.status_code}")
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return

    try:
        data = resp.json()
    except ValueError:
        print("❌ Response is not JSON")
        print(resp.text)
        return

    print("✅ Response JSON:")
    from pprint import pprint
    pprint(data)

if __name__ == "__main__":
    main()
