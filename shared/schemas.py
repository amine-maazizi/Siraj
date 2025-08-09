from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# ---- Ingest
class IngestResponse(BaseModel):
    doc_id: str
    title: str
    pages: int
    chunks: int

# ---- Summarize
class SummarizeRequest(BaseModel):
    doc_id: str

class SummarySection(BaseModel):
    title: str
    bullets: List[str] = Field(default_factory=list)

class SummarizeResponse(BaseModel):
    summary_sections: List[SummarySection] = Field(default_factory=list)

# ---- Chat
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatCitation(BaseModel):
    page: int
    snippet: str

class ChatRequest(BaseModel):
    doc_id: str
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    answer: str
    citations: List[ChatCitation] = Field(default_factory=list)

# ---- Quiz
class QuizOption(BaseModel):
    id: str
    text: str

class QuizQuestion(BaseModel):
    id: str
    stem: str
    options: List[QuizOption]
    multi: bool = True

class QuizGenerateRequest(BaseModel):
    doc_id: str
    n_questions: int = 6
    type: Literal["checkbox"] = "checkbox"

class QuizGenerateResponse(BaseModel):
    quiz_id: str
    questions: List[QuizQuestion]

class QuizAnswer(BaseModel):
    question_id: str
    option_ids: List[str]

class QuizGradeRequest(BaseModel):
    quiz_id: str
    answers: List[QuizAnswer]

class PerQuestionResult(BaseModel):
    id: str
    correct_option_ids: List[str]
    rationale: str

class QuizGradeResponse(BaseModel):
    score: int
    per_question: List[PerQuestionResult]

# ---- Progress
class ProgressTotals(BaseModel):
    docs: int
    quizzes: int
    avgScore: float

class ProgressHistoryPoint(BaseModel):
    date: str
    score: float

class ProgressSkill(BaseModel):
    name: str
    level: float

class ProgressGap(BaseModel):
    topic: str
    note: str

class ProgressResponse(BaseModel):
    totals: ProgressTotals
    history: List[ProgressHistoryPoint]
    skills: List[ProgressSkill]
    gaps: List[ProgressGap]

# ---- Suggestions
class SuggestRequest(BaseModel):
    gaps: List[str]
    time_per_day: int
    horizon_weeks: int

class PlanItem(BaseModel):
    week: int
    focus: str
    tasks: List[str]

class ResourceItem(BaseModel):
    title: str
    type: Literal["book", "video", "web"]
    link: Optional[str] = None

class SuggestResponse(BaseModel):
    plan: List[PlanItem]
    resources: List[ResourceItem]

# ---- Brainrot
BrainrotStyle = Literal["tldr", "memetic", "motivational"]

class BrainrotSummaryRequest(BaseModel):
    doc_id: str
    style: BrainrotStyle = "tldr"
    duration_sec: int = 30

class BrainrotSummaryResponse(BaseModel):
    job_id: str
    summary_text: str
    sections: List[SummarySection]

class BrainrotTTSRequest(BaseModel):
    job_id: str
    text: str
    voice: str = "en_female_1"
    speed: float = 1.0

class BrainrotTTSResponse(BaseModel):
    audio_path: str
    duration_ms: int

class BrainrotCaptionsRequest(BaseModel):
    job_id: str
    audio_path: str
    text: str
    level: Literal["line", "word"] = "line"

class BrainrotCaptionsResponse(BaseModel):
    vtt_path: str
    srt_path: str

class BrainrotRenderRequest(BaseModel):
    job_id: str
    audio_path: str
    vtt_path: str
    aspect: Literal["9:16", "16:9"] = "9:16"
    theme: str = "siraj"
    include_waveform: bool = True

class BrainrotRenderResponse(BaseModel):
    video_path: str
    thumbnail_path: Optional[str] = None
    duration_ms: int