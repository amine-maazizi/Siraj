from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid

from ..services.brainrot import (
    BrainrotManifest, save_manifest, load_manifest, manifest_path, DIRS,
    build_script_with_llm, synthesize_tts,
    captions_with_aeneas, captions_vtt_fallback, render_video, AENEAS_AVAILABLE
)

router = APIRouter(prefix="/brainrot", tags=["brainrot"])

class SummaryReq(BaseModel):
    doc_id: str
    style: str | None = "memetic"
    duration_sec: int | None = 30

@router.post("/summary")
def brainrot_summary(req: SummaryReq):
    job_id = uuid.uuid4().hex
    script_text, sections = build_script_with_llm(req.doc_id, req.style or "memetic", req.duration_sec or 30)
    m = BrainrotManifest(job_id=job_id, doc_id=req.doc_id, style=req.style or "memetic",
                         summary_text=script_text, sections=sections)
    save_manifest(m)
    return {"job_id": job_id, "summary_text": script_text, "sections": sections}

class TTSReq(BaseModel):
    job_id: str
    text: str
    voice: str | None = "en_female_1"
    speed: float | None = 1.0

@router.post("/tts")
def brainrot_tts(req: TTSReq):
    m = load_manifest(req.job_id)
    out_wav = os.path.join(DIRS["audio"], f"{req.job_id}.wav")
    duration_ms = synthesize_tts(req.text, out_wav, voice=req.voice or "en_female_1", speed=req.speed or 1.0)
    m.audio_path = out_wav
    m.duration_ms = duration_ms
    m.voice = req.voice or "en_female_1"
    m.speed = req.speed or 1.0
    save_manifest(m)
    return {"audio_path": out_wav, "duration_ms": duration_ms}

class CaptionsReq(BaseModel):
    job_id: str
    text: str
    level: str | None = "line"  # or "word"

@router.post("/captions")
def brainrot_captions(req: CaptionsReq):
    m = load_manifest(req.job_id)
    if not m.audio_path:
        raise HTTPException(400, "Missing audio. Call /brainrot/tts first.")
    if AENEAS_AVAILABLE:
        vtt_path, srt_path = captions_with_aeneas(req.text, m.audio_path, level=req.level or "line")
    else:
        vtt_path, srt_path = captions_vtt_fallback(req.text, m.duration_ms or 30000, level=req.level or "line")
    m.vtt_path = vtt_path
    m.srt_path = srt_path
    save_manifest(m)
    return {"vtt_path": vtt_path, "srt_path": srt_path}

class RenderReq(BaseModel):
    job_id: str
    aspect: str | None = "9:16"   # "9:16" | "16:9"
    include_waveform: bool | None = False
    theme: str | None = "siraj"

@router.post("/render")
def brainrot_render(req: RenderReq):
    m = load_manifest(req.job_id)
    if not m.audio_path or not m.vtt_path:
        raise HTTPException(400, "Missing audio or captions. Call /tts and /captions first.")
    out_mp4 = os.path.join(DIRS["video"], f"{req.job_id}.mp4")
    thumb = os.path.join(DIRS["thumbs"], f"{req.job_id}.png")
    duration_ms = render_video(m.audio_path, m.vtt_path, out_mp4, aspect=req.aspect or "9:16",
                               include_waveform=req.include_waveform or False, thumbnail_out=thumb)
    m.video_path = out_mp4
    m.thumbnail_path = thumb
    m.aspect = req.aspect or "9:16"
    m.duration_ms = duration_ms
    save_manifest(m)
    return {"video_path": out_mp4, "thumbnail_path": thumb, "duration_ms": duration_ms}

@router.get("/{job_id}")
def brainrot_stream(job_id: str):
    m = load_manifest(job_id)
    if not m.video_path or not os.path.exists(m.video_path):
        raise HTTPException(404, "Video not found. Did you call /render?")
    return FileResponse(m.video_path, media_type="video/mp4", filename=f"{job_id}.mp4")

@router.get("/{job_id}.vtt")
def brainrot_vtt(job_id: str):
    m = load_manifest(job_id)
    if not m.vtt_path or not os.path.exists(m.vtt_path):
        raise HTTPException(404, "Captions not found. Did you call /captions?")
    return FileResponse(m.vtt_path, media_type="text/vtt", filename=f"{job_id}.vtt")
