# tests/test_quiz.py
import os
import sys
import requests

BASE_URL = os.getenv("API_BASE", "http://localhost:8000")

def get_first_doc_id():
    r = requests.get(f"{BASE_URL}/documents")
    r.raise_for_status()
    docs = r.json()
    if not docs:
        raise RuntimeError("No documents found. Ingest a PDF first.")
    return docs[0]["doc_id"]

def generate_quiz(doc_id, n_questions=10):
    payload = {"doc_id": doc_id, "n_questions": n_questions, "type": "checkbox"}
    r = requests.post(f"{BASE_URL}/quiz/generate", json=payload)
    if r.status_code != 200:
        raise RuntimeError(f"Generate failed: {r.status_code} {r.text}")
    return r.json()

def grade_quiz(quiz_id, answers):
    payload = {"quiz_id": quiz_id, "answers": answers}
    r = requests.post(f"{BASE_URL}/quiz/grade", json=payload)
    if r.status_code != 200:
        raise RuntimeError(f"Grade failed: {r.status_code} {r.text}")
    return r.json()

def assert_quiz_shape(quiz, expected_n=10):
    assert "quiz_id" in quiz and quiz["quiz_id"], "Missing quiz_id"
    qs = quiz.get("questions", [])
    assert len(qs) == expected_n, f"Expected {expected_n} questions, got {len(qs)}"
    for i, q in enumerate(qs, 1):
        assert "id" in q and q["id"], f"Q{i} missing id"
        assert "stem" in q and q["stem"], f"Q{i} missing stem"
        opts = q.get("options", [])
        assert len(opts) == 4, f"Q{i} should have 4 options, got {len(opts)}"
        labels = {o.get("id") for o in opts}
        assert labels == {"A", "B", "C", "D"}, f"Q{i} option labels must be A-D, got {labels}"

def build_empty_answers(quiz):
    return [{"question_id": q["id"], "option_ids": []} for q in quiz["questions"]]

def build_correct_answers_from_grade(grade_result):
    """Use the first grade response (with empty answers) to extract correct_option_ids."""
    correct_by_q = {}
    for pq in grade_result.get("per_question", []):
        correct_by_q[pq["id"]] = pq["correct_option_ids"]
    answers = [{"question_id": qid, "option_ids": correct_by_q[qid]} for qid in correct_by_q]
    return answers

def main():
    # Allow overriding doc_id via CLI: python tests/test_quiz.py DOC_ID
    doc_id = sys.argv[1] if len(sys.argv) > 1 else get_first_doc_id()
    print(f"[i] Using doc_id: {doc_id}")

    # 1) Generate quiz (10 Q)
    quiz = generate_quiz(doc_id, n_questions=10)
    print(f"[i] Generated quiz_id: {quiz['quiz_id']}")
    assert_quiz_shape(quiz, expected_n=10)
    print("[✓] Quiz shape OK (10 questions, each 4 options A–D)")

    # 2) First grade pass with empty answers (to fetch solution keys)
    empty_answers = build_empty_answers(quiz)
    grade1 = grade_quiz(quiz["quiz_id"], empty_answers)
    print(f"[i] First grade score (empty answers): {grade1.get('score')}%")
    assert len(grade1.get("per_question", [])) == 10, "per_question should list all 10 items"
    print("[✓] Grade response shape OK")

    # 3) Build correct answers from grade1, then grade again to hit 100%
    correct_answers = build_correct_answers_from_grade(grade1)
    grade2 = grade_quiz(quiz["quiz_id"], correct_answers)
    print(f"[i] Second grade score (correct answers): {grade2.get('score')}%")

    # 4) Expect perfect score (100.0)
    assert float(grade2.get("score", 0)) == 100.0, f"Expected 100.0, got {grade2.get('score')}"
    print("[✓] Perfect score achieved with correct answers")

    # 5) Spot-check rationale presence
    missing_rationale = [pq["id"] for pq in grade2.get("per_question", []) if not pq.get("rationale")]
    assert not missing_rationale, f"Missing rationale for questions: {missing_rationale}"
    print("[✓] Rationales present for all questions")

    print("\nAll quiz API tests passed ✅")

if __name__ == "__main__":
    main()
