# Siraj – Local-First Study Companion

## Overview
Siraj is a **web-based learning companion** designed to help users study a specific subject by:
1. Uploading resources (PDFs, notes, descriptions).
2. Generating summaries and/or **Brainrot-style** video recaps.
3. Allowing conversational Q&A with an LLM (RAG-enabled with your documents).
4. Generating quizzes to test understanding.
5. Saving progress and results locally.
6. Providing targeted review & recommendations.
7. Displaying progress statistics in a dashboard.

Each project is stored locally as a `.sirajproj` file (SQLite or JSON) containing:
- **Metadata**: subject, goals, creation/modification dates.
- **Files**: uploaded resources.
- **Study data**: summaries, chats, quizzes, reviews, recommendations.
- **Progress tracking**: attempts history, streaks, skills mastered.

## Main User Flow
1. **Create Project** → enter subject & goals, optionally enable Brainrot.
2. **Upload Content** → PDFs/text ingested into a local vector DB.
3. **Summary/Brainrot Tab** → text or video summaries.
4. **Q&A** → ask questions, get citations, track sentiment.
5. **Quiz** → auto-generated MCQs with explanations.
6. **Review** → weak topics with targeted references.
7. **Recommendations** → AI-curated resources & weekly plan.
8. **Dashboard** → charts, completion %, streaks, skill mastery.

## Tech Stack
**Frontend**
- Next.js (App Router) + React + TypeScript
- TailwindCSS + shadcn/ui
- TanStack Query, react-hook-form
- PDF.js viewer, Recharts
- Video.js / native `<video>` with WebVTT captions
- (Optional) wavesurfer.js for waveform scrubbing
- Framer Motion for UI animations

**Backend**
- FastAPI + LangChain (thin layer)
- Ollama (local LLM: Llama 3.1 8B Instruct)
- Embeddings: nomic-embed-text or bge-small
- Chroma (local vector DB)
- PyPDF, unstructured, Tesseract (OCR)
- Instructor (Pydantic) for structured outputs
- Coqui TTS (XTTS v2), ffmpeg, moviepy, aeneas, pydub, pysubs2, Pillow
- Transformers/VADER for sentiment analysis

**Storage**
- SQLite (inside `.sirajproj`)
- Chroma persist directory
- Media folders: `/audio`, `/subs`, `/video`, `/assets`

**System Dependencies**
- ffmpeg
- espeak (for aeneas)
- sox (optional, for aeneas)

## Demo Targets
- Upload PDF → preview → “Ingested: N chunks”
- Summarize → 2–3 section bullets
- Chat → citations from PDF
- Generate quiz → answer & grade with rationale
- Dashboard → seeded history + new attempts
- Brainrot → create 30–45s MP4 with captions

---
