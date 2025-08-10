from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from ..services.quizgen import generate_quiz_from_doc, QuizSpec

router = APIRouter(prefix="/quiz", tags=["quiz"])

# naive in-memory cache for grading during a session
QUIZ_CACHE: Dict[str, QuizSpec] = {}

class QuizGenerateRequest(BaseModel):
    doc_id: str
    n_questions: int = 10
    type: str = "checkbox"  # for future types

class QuizOptionView(BaseModel):
    id: str
    text: str

class QuizQuestionView(BaseModel):
    id: str
    stem: str
    options: List[QuizOptionView]
    multi: bool = True

class QuizGenerateResponse(BaseModel):
    quiz_id: str
    questions: List[QuizQuestionView]

@router.post("/generate", response_model=QuizGenerateResponse)
def generate(req: QuizGenerateRequest):
    if not req.doc_id:
        raise HTTPException(status_code=400, detail="doc_id required")
    spec = generate_quiz_from_doc(req.doc_id, n_questions=req.n_questions or 10)
    QUIZ_CACHE[spec.quiz_id] = spec
    return QuizGenerateResponse(
        quiz_id=spec.quiz_id,
        questions=[
            QuizQuestionView(
                id=q.id,
                stem=q.stem,
                options=[QuizOptionView(id=o.id, text=o.text) for o in q.options],
                multi=True,
            )
            for q in spec.questions
        ]
    )

# ---- Grading

class QuizAnswer(BaseModel):
    question_id: str
    option_ids: List[str] = []  # selected

class QuizGradeRequest(BaseModel):
    quiz_id: str
    answers: List[QuizAnswer]

class PerOptionResult(BaseModel):
    id: str
    text: str
    selected: bool
    correct: bool

class PerQuestionResult(BaseModel):
    id: str
    correct_option_ids: List[str]
    rationale: str
    options: List[PerOptionResult]

class QuizGradeResponse(BaseModel):
    score: float  # percentage 0..100
    per_question: List[PerQuestionResult]

@router.post("/grade", response_model=QuizGradeResponse)
def grade(req: QuizGradeRequest):
    spec = QUIZ_CACHE.get(req.quiz_id)
    if not spec:
        raise HTTPException(status_code=404, detail="quiz_id not found (cache expired)")

    # map answers
    ans_map = {a.question_id: set(a.option_ids or []) for a in req.answers}

    per_q = []
    n_correct = 0
    for q in spec.questions:
        selected = ans_map.get(q.id, set())
        correct_set = set(q.correct_option_ids)
        is_correct = (selected == correct_set)
        if is_correct:
            n_correct += 1

        options_result = []
        for o in q.options:
            options_result.append(PerOptionResult(
                id=o.id,
                text=o.text,
                selected=(o.id in selected),
                correct=(o.id in correct_set),
            ))
        per_q.append(PerQuestionResult(
            id=q.id,
            correct_option_ids=q.correct_option_ids,
            rationale=q.rationale,
            options=options_result,
        ))

    score = round(100.0 * n_correct / max(1, len(spec.questions)), 1)
    return QuizGradeResponse(score=score, per_question=per_q)
