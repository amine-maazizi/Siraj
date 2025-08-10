#!/usr/bin/env python3
"""
Simple router endpoint test for the Brainrot pipeline (no pytest).
- Calls FastAPI endpoints directly via HTTP.
- Saves outputs to ./_out
- Modes:
   --mode light  : /brainrot/summary only
   --mode full   : /summary -> /tts -> /captions -> /render -> GET mp4+vtt
"""

import argparse
import json
import os
import shutil
import sys
import time
from urllib.parse import urljoin

import requests


def info(msg):  print(f"[INFO] {msg}")
def ok(msg):    print(f"[PASS] {msg}")
def fail(msg):  print(f"[FAIL] {msg}")


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000", help="FastAPI base URL")
    ap.add_argument("--doc-id", default="doc_demo", help="doc_id to summarize")
    ap.add_argument("--style", default="memetic", help="script style")
    ap.add_argument("--duration", type=int, default=30, help="target seconds")
    ap.add_argument("--mode", choices=["light", "full"], default="full")
    ap.add_argument("--aspect", choices=["9:16","16:9"], default="9:16")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    out_dir = os.path.abspath("./_out")
    os.makedirs(out_dir, exist_ok=True)

    # 1) /brainrot/summary
    info("Calling /brainrot/summary …")
    r = requests.post(
        urljoin(base, "/brainrot/summary"),
        json={"doc_id": args.doc_id, "style": args.style, "duration_sec": args.duration},
        timeout=120,
    )
    if r.status_code != 200:
        fail(f"/brainrot/summary HTTP {r.status_code}: {r.text[:500]}")
        return 1
    data = r.json()
    job_id = data.get("job_id")
    script = data.get("summary_text", "")
    if not job_id or not script:
        fail("Missing job_id or summary_text in /summary response")
        return 1
    ok(f"/brainrot/summary OK (job_id={job_id})")

    if args.mode == "light":
        info("Light mode done.")
        return 0

    # 2) /brainrot/tts
    info("Calling /brainrot/tts …")
    try:
        r = requests.post(
            urljoin(base, "/brainrot/tts"),
            json={"job_id": job_id, "text": script, "voice": "en_female_1", "speed": 1.0},
            timeout=300,
        )
    except requests.exceptions.RequestException as e:
        fail(f"/brainrot/tts request error: {e}")
        print("\nHint: install Coqui TTS (xtts_v2) in your server venv.\n"
              "  pip install tts[all]\n"
              "Also ensure ffmpeg is installed and on PATH. :contentReference[oaicite:1]{index=1}")
        return 2

    if r.status_code != 200:
        fail(f"/brainrot/tts HTTP {r.status_code}: {r.text[:500]}")
        print("\nLikely Coqui TTS or ffmpeg missing in the server env. :contentReference[oaicite:2]{index=2}")
        return 2
    tts = r.json()
    audio_path = tts.get("audio_path")
    duration_ms = tts.get("duration_ms")
    if not audio_path or not duration_ms:
        fail("Missing audio_path/duration_ms from /tts")
        return 2
    ok(f"/brainrot/tts OK (audio={audio_path}, duration={duration_ms} ms)")

    # 3) /brainrot/captions
    info("Calling /brainrot/captions …")
    r = requests.post(
        urljoin(base, "/brainrot/captions"),
        json={"job_id": job_id, "text": script, "level": "line"},
        timeout=180,
    )
    if r.status_code != 200:
        fail(f"/brainrot/captions HTTP {r.status_code}: {r.text[:500]}")
        print("\nIf aeneas is not installed, the server should fall back to basic timing.\n"
              "To enable forced alignment, install aeneas + espeak-ng (+ optional sox). :contentReference[oaicite:3]{index=3}")
        return 3
    caps = r.json()
    vtt_path = caps.get("vtt_path")
    srt_path = caps.get("srt_path")
    if not vtt_path or not srt_path:
        fail("Missing vtt_path/srt_path from /captions")
        return 3
    ok(f"/brainrot/captions OK (vtt={vtt_path})")

    # 4) /brainrot/render  (requires ffmpeg on server PATH)
    info("Calling /brainrot/render …")
    if not has_ffmpeg():
        info("Local ffmpeg not detected; render still runs server-side if its PATH is set. :contentReference[oaicite:4]{index=4}")
    r = requests.post(
        urljoin(base, "/brainrot/render"),
        json={"job_id": job_id, "aspect": args.aspect, "include_waveform": False},
        timeout=600,
    )
    if r.status_code != 200:
        fail(f"/brainrot/render HTTP {r.status_code}: {r.text[:500]}")
        print("\nEnsure ffmpeg is installed on the server host and visible to the FastAPI process. :contentReference[oaicite:5]{index=5}")
        return 4
    rend = r.json()
    video_path = rend.get("video_path")
    thumb_path = rend.get("thumbnail_path")
    if not video_path or not thumb_path:
        fail("Missing video_path/thumbnail_path from /render")
        return 4
    ok(f"/brainrot/render OK (video={video_path})")

    # 5) GET /brainrot/{id}  +  {id}.vtt
    mp4_out = os.path.join(out_dir, f"{job_id}.mp4")
    vtt_out = os.path.join(out_dir, f"{job_id}.vtt")

    info("Downloading MP4 …")
    r = requests.get(urljoin(base, f"/brainrot/{job_id}"), timeout=600)
    if r.status_code != 200 or "video/mp4" not in r.headers.get("content-type",""):
        fail(f"GET /brainrot/{job_id} failed: HTTP {r.status_code}")
        return 5
    with open(mp4_out, "wb") as f:
        f.write(r.content)

    info("Downloading VTT …")
    r = requests.get(urljoin(base, f"/brainrot/{job_id}.vtt"), timeout=120)
    if r.status_code != 200 or "text/vtt" not in r.headers.get("content-type",""):
        fail(f"GET /brainrot/{job_id}.vtt failed: HTTP {r.status_code}")
        return 5
    with open(vtt_out, "wb") as f:
        f.write(r.content)

    ok(f"Stream endpoints OK → saved:\n  {mp4_out}\n  {vtt_out}")

    # Heads-up about background template
    assets_hint = os.path.join("server", "media", "assets", "bg_loop.mp4")
    if os.path.exists(assets_hint):
        info(f"Background template detected: {assets_hint}")
    else:
        info(f"No bg template found. Optional file for on-brand look:\n  {assets_hint}\n"
             "Renderer will use an animated gradient if missing.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
