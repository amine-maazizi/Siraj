#!/usr/bin/env bash
# setup.sh — Repo-level scaffold for Siraj
set -euo pipefail

echo ">> Creating .env.example"
cat <<'EOF' > .env.example
# --- Siraj env (copy to .env) ---
SIRAJ_PROJECTS_DIR=./SirajProjects
CHROMA_DIR=server/store/chroma

# Models (Ollama)
LLM_MODEL=llama3.1
EMBED_MODEL=nomic-embed-text

# Brainrot defaults
BRAINROT_VOICE=en_female_1
BRAINROT_SPEED=1.0
BRAINROT_ASPECT=9:16
BRAINROT_THEME=siraj

# API
API_HOST=0.0.0.0
API_PORT=8000
EOF

echo ">> Creating .gitignore"
cat <<'EOF' > .gitignore
# Python
.venv/
__pycache__/
*.pyc

# Node / Next.js
app/node_modules/
app/.next/
app/.vercel/

# Env & local
.env
.env.local
*.sirajproj
SirajProjects/
server/store/chroma/
server/media/
.DS_Store

# Editors
.vscode/
.idea/
EOF

echo ">> Creating .pre-commit-config.yaml"
cat <<'EOF' > .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.6
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
EOF

echo ">> Creating LICENSE (MIT)"
cat <<'EOF' > LICENSE
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is furnished
to do so, subject to the following conditions:

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND.
EOF

echo ">> Creating README.md"
cat <<'EOF' > README.md
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
EOF

echo "✅ Repo-level files created: .env.example, .gitignore, .pre-commit-config.yaml, LICENSE, README.md"
