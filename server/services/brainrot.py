# server/services/brainrot.py

import json
import os
import uuid
import threading
from dataclasses import dataclass, asdict
from typing import Optional, Tuple

import numpy as np
import pyttsx3
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
from moviepy import (
    AudioFileClip,
    VideoFileClip,
    ImageClip,
    CompositeVideoClip,
    ColorClip,
)
import moviepy.video.fx as vfx
import pysubs2

from server.services.llm_brainrot import brainrot_summary as _brainrot_summary

# aeneas is optional; we try-import
try:
    from aeneas.executetask import ExecuteTask
    from aeneas.task import Task
    AENEAS_AVAILABLE = True
except Exception:
    AENEAS_AVAILABLE = False


HERE = os.path.dirname(__file__)
MEDIA_ROOT = os.path.normpath(os.path.join(HERE, "..", "media"))
DIRS = {
    "audio": os.path.join(MEDIA_ROOT, "audio"),
    "subs": os.path.join(MEDIA_ROOT, "subs"),
    "video": os.path.join(MEDIA_ROOT, "video"),
    "assets": os.path.join(MEDIA_ROOT, "assets"),
    "thumbs": os.path.join(MEDIA_ROOT, "thumbs"),
    "manifests": os.path.join(MEDIA_ROOT, "manifests"),
}
BG_LOOP_PATH = os.path.join(DIRS["assets"], "bg_loop.mp4")  # optional


def _ensure_dirs():
    for p in DIRS.values():
        os.makedirs(p, exist_ok=True)


# ---------- Manifest ----------

@dataclass
class BrainrotManifest:
    job_id: str
    doc_id: Optional[str]
    style: str
    summary_text: Optional[str] = None
    sections: Optional[list] = None
    audio_path: Optional[str] = None
    vtt_path: Optional[str] = None
    srt_path: Optional[str] = None
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    duration_ms: Optional[int] = None
    aspect: Optional[str] = "9:16"
    voice: Optional[str] = "female"   # pyttsx3 hint
    speed: float = 1.0


def manifest_path(job_id: str) -> str:
    _ensure_dirs()
    return os.path.join(DIRS["manifests"], f"{job_id}.json")


def save_manifest(m: BrainrotManifest) -> None:
    _ensure_dirs()
    with open(manifest_path(m.job_id), "w", encoding="utf-8") as f:
        json.dump(asdict(m), f, ensure_ascii=False, indent=2)


def load_manifest(job_id: str) -> BrainrotManifest:
    with open(manifest_path(job_id), "r", encoding="utf-8") as f:
        data = json.load(f)
    return BrainrotManifest(**data)


# -------- SUMMARY (script) -------

def build_script_with_llm(doc_id: str, style: str, duration_sec: int):
    return _brainrot_summary(doc_id=doc_id, style=style, duration_sec=duration_sec)


# -------- TTS (pyttsx3 - offline) --------

_TTS_ENGINE = None
_TTS_LOCK = threading.Lock()


def _get_tts_engine():
    """
    pyttsx3 engine singleton. Force Windows SAPI5 driver to avoid KeyError: None.
    On macOS/Linux, pyttsx3 will fallback to NSSpeech/eSpeak automatically.
    """
    global _TTS_ENGINE
    if _TTS_ENGINE is not None:
        return _TTS_ENGINE
    with _TTS_LOCK:
        if _TTS_ENGINE is None:
            try:
                # On Windows this ensures SAPI is used; elsewhere it is ignored.
                eng = pyttsx3.init(driverName="sapi5")
            except Exception:
                # Fallback if not on Windows or sapi5 unavailable.
                eng = pyttsx3.init()
            eng.setProperty("volume", 1.0)
            _TTS_ENGINE = eng
    return _TTS_ENGINE


def _select_voice(engine: pyttsx3.Engine, voice_hint: Optional[str]) -> Optional[str]:
    """
    Try to pick a voice by substring match on name/id/languages.
    Examples: 'female', 'male', 'en', 'fr', 'zira', 'david'
    """
    if not voice_hint:
        return None
    hint = voice_hint.lower()
    for v in engine.getProperty("voices"):
        name = (getattr(v, "name", "") or "").lower()
        vid = (getattr(v, "id", "") or "").lower()
        langs_raw = getattr(v, "languages", []) or []
        langs = " ".join([str(x) for x in langs_raw]).lower()
        if hint in name or hint in vid or hint in langs:
            return v.id
    return None


def synthesize_tts(text: str, out_wav: str, voice: str = "female", speed: float = 1.0) -> int:
    """
    Generate WAV with system TTS, then normalize to ~-14 dBFS.
    - voice: substring hint (e.g., 'female', 'male', 'en', 'fr', 'Zira', 'David').
    - speed: 1.0 = base rate. <1 slower, >1 faster.
    Returns duration in milliseconds.
    """
    engine = _get_tts_engine()

    # Adjust rate (pyttsx3 uses WPM-ish integer)
    base_rate = engine.getProperty("rate") or 200
    target_rate = max(80, int(base_rate * speed))
    engine.setProperty("rate", target_rate)

    # Voice selection (best-effort)
    voice_id = _select_voice(engine, voice)
    if voice_id:
        engine.setProperty("voice", voice_id)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)

    # Synthesize to file (blocking)
    engine.save_to_file(text, out_wav)
    engine.runAndWait()

    # Loudness normalize to roughly -14 dBFS (proxy for -14 LUFS)
    seg = AudioSegment.from_file(out_wav)
    gain = -14.0 - seg.dBFS
    seg = seg.apply_gain(gain)
    seg.export(out_wav, format="wav")

    return int(len(seg))  # ms


# -------- CAPTIONS --------

def captions_vtt_fallback(text: str, audio_ms: int, level: str = "line") -> Tuple[str, str]:
    """
    Evenly distribute lines over total duration; simple, deterministic fallback.
    """
    _ensure_dirs()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    n = max(1, len(lines))
    step = max(1, audio_ms // n)
    subs = pysubs2.SSAFile()
    t = 0
    for line in lines:
        start = t
        end = min(audio_ms, start + step)
        ev = pysubs2.SSAEvent(start=start, end=end, text=line)
        subs.events.append(ev)
        t += step
    vtt_path = os.path.join(DIRS["subs"], f"{uuid.uuid4().hex}.vtt")
    srt_path = vtt_path.replace(".vtt", ".srt")
    subs.save(srt_path, format_="srt")
    subs.save(vtt_path, format_="vtt")
    return vtt_path, srt_path


def captions_with_aeneas(text: str, audio_path: str, level: str = "line") -> Tuple[str, str]:
    if not AENEAS_AVAILABLE:
        # fallback to naive timing if aeneas missing
        seg = AudioSegment.from_file(audio_path)
        return captions_vtt_fallback(text, int(len(seg)), level=level)

    _ensure_dirs()
    # Write text to temp file
    txt_path = os.path.join(DIRS["subs"], f"{uuid.uuid4().hex}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    vtt_path = os.path.join(DIRS["subs"], f"{uuid.uuid4().hex}.vtt")
    srt_path = vtt_path.replace(".vtt", ".srt")

    # aeneas config
    granularity = "word" if level == "word" else "sentence"
    task = Task(
        config_string=(
            "task_language=eng|is_text_type=plain|os_task_file_format=vtt|"
            "task_adjust_boundary_algorithm=percent|task_adjust_boundary_percent_value=50|"
            "task_adjust_boundary_nonspeech_min=0.1|task_adjust_boundary_nonspeech_string=REMOVE|"
            "task_adjust_boundary_string=AVERAGE|task_adjust_boundary_algorithm_value=0.2|"
            "task_adjust_boundary_string_value=0.2|"
            f"task_description={granularity}"
        )
    )
    task.audio_file_path_absolute = audio_path
    task.text_file_path_absolute = txt_path
    task.sync_map_file_path_absolute = vtt_path
    ExecuteTask(task).execute()

    # Convert to SRT using pysubs2
    subs = pysubs2.load(vtt_path, encoding="utf-8")
    subs.save(srt_path, format_="srt")
    return vtt_path, srt_path


# -------- RENDER --------

def _ensure_aspect(w: int, h: int, aspect: str) -> Tuple[int, int]:
    if aspect == "16:9":
        return 1920, 1080
    return 1080, 1920  # 9:16 default


def _make_bg_clip(duration: float, aspect: str):
    # Prefer asset loop if present
    W, H = _ensure_aspect(0, 0, aspect)
    if os.path.exists(BG_LOOP_PATH):
        clip = VideoFileClip(BG_LOOP_PATH).without_audio()
        if clip.duration < duration:
            # Proper loop effect
            clip = vfx.loop(clip, duration=duration)
        else:
            clip = clip.subclipped(0, duration)

        # Resize and crop to target aspect ratio
        clip = clip.resized(height=H)
        if clip.w > W:
            x_center = clip.w / 2
            clip = clip.cropped(width=W, height=H, x_center=x_center, y_center=H / 2)

        return clip

    # Procedural: minimal animated overlay on deep indigo bg
    base = ColorClip(size=(W, H), color=(26, 14, 46), duration=duration)  # deep indigo

    # Create animated overlay
    overlay_w = int(W * 0.9)
    overlay_h = int(H * 0.12)
    overlay = ColorClip(size=(overlay_w, overlay_h), color=(255, 180, 84), duration=duration)  # amber bar

    # Simple horizontal movement animation
    def move_overlay(t):
        x_offset = int((W * 0.05) + (W * 0.02) * ((t * 0.5) % 1))  # Slower movement
        y_offset = int(H * 0.1)
        return (x_offset, y_offset)

    overlay = overlay.with_position(move_overlay)
    return CompositeVideoClip([base, overlay])



def render_video(
    audio_path: str,
    vtt_path: str,
    out_mp4: str,
    aspect: str = "9:16",
    include_waveform: bool = False,  # reserved for future (wavesurfer export)
    thumbnail_out: Optional[str] = None,
) -> int:
    _ensure_dirs()
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    bg = _make_bg_clip(duration, aspect)
    W, H = bg.size

    overlays = _burn_captions(vtt_path, W, H)
    comp = CompositeVideoClip([bg, *overlays]).with_audio(audio)
    comp.write_videofile(
        out_mp4,
        fps=30,
        audio_codec="aac",
        codec="libx264",
        preset="veryfast",
        # threads parameter is deprecated/unused in v2; rely on defaults
    )

    if thumbnail_out:
        # In v2, prefer write_image; save_frame still works, but this is future-proof.
        try:
            comp.write_image(thumbnail_out, t=min(1.0, max(0.0, duration / 2)))
        except Exception:
            comp.save_frame(thumbnail_out, t=min(1.0, max(0.0, duration / 2)))

    comp.close()
    bg.close()
    audio.close()
    return int(duration * 1000)


def _burn_captions(vtt_path: str, W: int, H: int):
    """
    Render BIG captions at the top with an opaque black bar.
    Requires a TTF/OTF font in assets.
    """
    subs = pysubs2.load(vtt_path, encoding="utf-8")
    clips = []

    # === SETTINGS ===
    pad = int(H * 0.02)
    bar_h = int(H * 0.30)              # 30% of video height
    base_font_ratio = 0.12             # 12% of height (VERY BIG)
    max_lines = 3
    text_box_w = int(W * 0.96)
    line_spacing_ratio = 0.28
    bar_color = (0, 0, 0, 255)         # solid black
    text_color = (255, 255, 255, 255)  # white
    # =================

    # Load scalable font
    font_path = os.path.join(DIRS["assets"], "PressStart2P-Regular.ttf")  # change if you use another font
    if not os.path.exists(font_path):
        raise FileNotFoundError(
            f"Font file not found: {font_path}\n"
            f"Please place a TTF/OTF font in {DIRS['assets']} and update _burn_captions."
        )

    def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int):
        words = text.replace("\n", " ").split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    for ev in subs.events:
        start = ev.start / 1000.0
        end = ev.end / 1000.0

        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, "RGBA")

        # Top bar
        bar_y = pad
        draw.rectangle([(0, bar_y), (W, bar_y + bar_h)], fill=bar_color)

        # Start with big font size
        font_px = int(H * base_font_ratio)
        font = ImageFont.truetype(font_path, size=font_px)
        spacing = int(font_px * line_spacing_ratio)

        # Wrap text to fit width
        lines = wrap_text(draw, ev.text, font, text_box_w)

        # Shrink font only if needed to fit height or lines limit
        while True:
            wrapped = "\n".join(lines[:max_lines])
            bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=spacing, align="center")
            text_h = bbox[3] - bbox[1]
            if text_h <= bar_h * 0.9 and len(lines) <= max_lines:
                break
            font_px -= 4
            font = ImageFont.truetype(font_path, size=font_px)
            spacing = int(font_px * line_spacing_ratio)
            lines = wrap_text(draw, ev.text, font, text_box_w)
            if font_px < 20:
                break

        wrapped = "\n".join(lines[:max_lines])
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=spacing, align="center")
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = (W - text_w) // 2
        text_y = bar_y + (bar_h - text_h) // 2

        draw.multiline_text(
            (text_x, text_y),
            wrapped,
            font=font,
            fill=text_color,
            align="center",
            spacing=spacing,
        )

        frame = np.array(img)
        clip = (
            ImageClip(frame)
            .with_start(start)
            .with_end(end)
            .with_position((0, 0))
        )
        clips.append(clip)

    return clips
