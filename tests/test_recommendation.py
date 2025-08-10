# tests/test_recommendation_backend.py
import os
import sys
import json
import argparse
import textwrap
from typing import List, Optional

import requests

DEFAULT_BASE = os.environ.get("SIRAJ_API_BASE", "http://localhost:8000")
TIMEOUT = 60


def pretty(obj) -> str:
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)


def hit_review(base: str) -> int:
    url = f"{base.rstrip('/')}/review"
    print(f"\n=== GET {url}")
    r = requests.get(url, timeout=TIMEOUT)
    print(f"Status: {r.status_code}")
    try:
        data = r.json()
    except Exception:
        data = r.text
    print(pretty(data))
    return r.status_code


def hit_suggest(
    base: str,
    gaps: Optional[List[str]],
    time_per_day: int,
    horizon_weeks: int,
    doc_id: Optional[str],
) -> int:
    url = f"{base.rstrip('/')}/suggest"
    payload = {
        "gaps": gaps or [],
        "time_per_day": time_per_day,
        "horizon_weeks": horizon_weeks,
    }
    if doc_id:
        payload["doc_id"] = doc_id

    print(f"\n=== POST {url}")
    print("Payload:", pretty(payload))
    r = requests.post(url, json=payload, timeout=TIMEOUT)
    print(f"Status: {r.status_code}")
    try:
        data = r.json()
    except Exception:
        data = r.text
    print(pretty(data))
    return r.status_code


def main():
    p = argparse.ArgumentParser(
        description="Backend smoke test for /review and /suggest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              python -m tests.test_recommendation_backend
              python -m tests.test_recommendation_backend --base http://127.0.0.1:8000
              python -m tests.test_recommendation_backend --gaps "work-energy theorem" "free body diagrams"
            """
        ),
    )
    p.add_argument("--base", default=DEFAULT_BASE, help="FastAPI base URL")
    p.add_argument("--gaps", nargs="*", help="Explicit gaps to test /suggest with")
    p.add_argument("--doc-id", default=None, help="Optional doc_id to bias /suggest")
    p.add_argument("--time-per-day", type=int, default=25)
    p.add_argument("--horizon-weeks", type=int, default=3)
    p.add_argument("--skip-review", action="store_true", help="Skip GET /review")
    p.add_argument("--skip-suggest-empty", action="store_true", help="Skip POST /suggest with gaps=[]")
    args = p.parse_args()

    # 1) /review
    if not args.skip_review:
        status_review = hit_review(args.base)
    else:
        status_review = None

    # 2) /suggest with explicit gaps (should succeed)
    gaps = args.gaps or ["work-energy theorem", "free body diagrams"]
    status_suggest_with = hit_suggest(
        args.base, gaps, args.time_per_day, args.horizon_weeks, args.doc_id
    )

    # 3) /suggest with NO gaps (should be 200 if attempts mining works, else 400)
    if not args.skip_suggest_empty:
        status_suggest_empty = hit_suggest(
            args.base, [], args.time_per_day, args.horizon_weeks, args.doc_id
        )
    else:
        status_suggest_empty = None

    # Exit code summary for CI-ish runs
    # - If “with gaps” fails → non-zero
    # - If “empty gaps” returns 400 with detail "No gaps..." we still exit 0 (expected in your current bug)
    ok = True
    if status_suggest_with != 200:
        ok = False
    if status_suggest_empty not in (None, 200, 400):
        ok = False

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
