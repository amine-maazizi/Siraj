# server/services/llm_brainrot.py
from __future__ import annotations
from typing import List, Tuple
import re
from server.services.llm import OllamaGenerateClient
from server.deps import get_vectordb

OLLAMA = OllamaGenerateClient(model="llama3.1", host="http://127.0.0.1:11434")

def _build_prompt(context: str, style: str, duration_sec: int) -> str:
    # cap words ~140 per 30s
    max_words = max(80, int(140 * (duration_sec / 30)))
    
    style_guides = {
        "memetic": "viral, engaging, relatable language with pop culture references",
        "educational": "clear, informative, but still energetic and accessible",
        "dramatic": "intense, emotional, storytelling approach with strong imagery",
        "conversational": "casual, friendly, like talking to a friend",
        "professional": "polished but accessible, authoritative yet engaging"
    }
    
    style_guide = style_guides.get(style, "engaging and energetic")
    
    return f"""Create a seamless, engaging {duration_sec}-second script that summarizes this document for a vertical video format.

Style: {style_guide}

Requirements:
- Natural flow from start to finish - NO rigid sections or labels
- Start with something immediately engaging that hooks attention
- Build momentum through the core content
- End with a satisfying conclusion or call-to-action
- Max {max_words} words total
- Simple, conversational language in present tense
- Break into natural speaking chunks (one thought per line)
- Each line should feel like a natural pause for captions

Context to summarize:
---
{context}
---

Write ONLY the script lines with no section labels, no markdown formatting, no "Hook:" or "Core:" labels. Make it flow like natural speech that someone would actually say."""


def _clean_script(script_text: str) -> str:
    """Remove any rigid formatting artifacts and make the script flow naturally."""
    lines = []
    for line in script_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
            
        # Remove any section labels that might have leaked through
        line = re.sub(r'^(Hook|Core|Close|Catch|Opening|Ending)\s*[:\-]\s*', '', line, flags=re.IGNORECASE)
        
        # Remove quotation marks if the entire line is quoted
        if line.startswith('"') and line.endswith('"') and line.count('"') == 2:
            line = line[1:-1]
        if line.startswith("'") and line.endswith("'") and line.count("'") == 2:
            line = line[1:-1]
            
        # Remove common artifacts
        line = re.sub(r'^[\-\*\•]\s*', '', line)  # Remove bullet points
        line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Remove numbered lists
        
        # Skip meta-commentary lines
        meta_patterns = [
            r'here\'s the script',
            r'script for',
            r'here are the lines',
            r'the following script',
            r'below is the',
            r'this script'
        ]
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in meta_patterns):
            continue
            
        if line:
            lines.append(line)
    
    return '\n'.join(lines)


def _generate_organic_sections(lines: List[str]) -> List[dict]:
    """Generate natural flow sections without rigid boundaries."""
    if len(lines) <= 3:
        return [{"title": "Complete", "bullets": lines}]
    
    # Natural flow: opening (25%), main content (50%), conclusion (25%)
    total = len(lines)
    opening_end = max(1, total // 4)
    conclusion_start = max(opening_end + 1, total - max(1, total // 4))
    
    sections = []
    
    if opening_end > 0:
        sections.append({
            "title": "Opening",
            "bullets": lines[:opening_end]
        })
    
    if conclusion_start > opening_end:
        sections.append({
            "title": "Main Content", 
            "bullets": lines[opening_end:conclusion_start]
        })
    
    if conclusion_start < total:
        sections.append({
            "title": "Conclusion",
            "bullets": lines[conclusion_start:]
        })
    
    return sections


def brainrot_summary(doc_id: str, style: str = "memetic", duration_sec: int = 30) -> Tuple[str, List[dict]]:
    # pull a few top chunks from this doc for context
    seed = "high level summary of this document"
    chunks = get_vectordb().similarity_search(seed, k=8, filter={"doc_id": doc_id}) or []
    context = "\n\n".join(c.page_content[:800] for c in chunks)

    prompt = _build_prompt(context, style, duration_sec)
    # NOTE: positional args like in summarize.py → (text, temperature, max_tokens)
    raw_script = OLLAMA.generate(prompt, 0.25, 320)
    
    # Clean and process the script
    script_text = _clean_script(raw_script)
    
    # Split into lines for sections
    lines = [ln.strip() for ln in script_text.splitlines() if ln.strip()]
    
    # Generate organic sections based on natural flow
    sections = _generate_organic_sections(lines)
    
    return script_text, sections
