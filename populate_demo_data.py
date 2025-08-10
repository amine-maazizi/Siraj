#!/usr/bin/env python3
"""
Populate demo data for dashboard progression.
This script creates realistic data for documents, quizzes, quiz attempts, and gaps
to demonstrate progression tracking, streaks, and learning analytics.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import List, Dict, Any

# Demo data for realistic content
DEMO_DOCUMENTS = [
    {
        "title": "Machine Learning Fundamentals",
        "topics": ["neural networks", "gradient descent", "overfitting", "regularization"],
        "difficulty": "beginner"
    },
    {
        "title": "Deep Learning with PyTorch",
        "topics": ["convolutional networks", "RNNs", "transformers", "optimization"],
        "difficulty": "intermediate"
    },
    {
        "title": "Natural Language Processing",
        "topics": ["tokenization", "embeddings", "attention mechanisms", "BERT"],
        "difficulty": "intermediate"
    },
    {
        "title": "Computer Vision Techniques",
        "topics": ["image preprocessing", "feature extraction", "object detection", "segmentation"],
        "difficulty": "intermediate"
    },
    {
        "title": "Advanced Deep Learning",
        "topics": ["GANs", "variational autoencoders", "reinforcement learning", "meta-learning"],
        "difficulty": "advanced"
    },
    {
        "title": "MLOps and Production",
        "topics": ["model deployment", "monitoring", "scaling", "versioning"],
        "difficulty": "intermediate"
    },
    {
        "title": "Research Paper Analysis",
        "topics": ["literature review", "methodology", "experimental design", "scientific writing"],
        "difficulty": "advanced"
    },
    {
        "title": "Statistics for ML",
        "topics": ["probability", "hypothesis testing", "bayesian inference", "experimental design"],
        "difficulty": "beginner"
    }
]

KNOWLEDGE_GAPS = [
    {"topic": "Mathematical Foundations", "note": "Need stronger understanding of linear algebra and calculus"},
    {"topic": "Model Interpretability", "note": "Requires more practice with SHAP and LIME techniques"},
    {"topic": "Advanced Optimization", "note": "Could benefit from studying Adam variants and learning rate scheduling"},
    {"topic": "Distributed Training", "note": "Need hands-on experience with multi-GPU and distributed setups"},
    {"topic": "Research Methodology", "note": "Should improve experimental design and statistical analysis skills"},
    {"topic": "Production Deployment", "note": "More experience needed with containerization and orchestration"},
    {"topic": "Data Engineering", "note": "Strengthen skills in data pipelines and feature engineering"},
    {"topic": "Domain Expertise", "note": "Develop deeper understanding of specific application areas"}
]

def get_db_path() -> str:
    """Get the database path, preferring existing files."""
    candidates = [
        Path(__file__).parent / "server" / "store" / "sqlite.db",
        Path(__file__).parent / "server" / "store" / "siraj.sqlite3",
    ]
    
    for p in candidates:
        if p.exists():
            return str(p)
    
    # Create the directory and return the first option
    candidates[0].parent.mkdir(parents=True, exist_ok=True)
    return str(candidates[0])

def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure all required tables exist with proper schema."""
    cur = conn.cursor()
    
    # Documents table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY,
            title TEXT,
            path TEXT,
            created_at TEXT
        )
    """)
    
    # Quizzes table (matching existing schema)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quizzes(
            id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            spec_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Quiz attempts table (matching existing schema)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts(
            id INTEGER PRIMARY KEY,
            quiz_id TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            score REAL NOT NULL,
            answers_json TEXT NOT NULL,
            feedback_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Gaps table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gaps(
            topic TEXT,
            note TEXT
        )
    """)
    
    conn.commit()

def generate_quiz_questions(doc_title: str, topics: List[str], difficulty: str) -> List[Dict[str, Any]]:
    """Generate realistic quiz questions based on document content."""
    questions = []
    
    # Base questions by difficulty
    if difficulty == "beginner":
        question_templates = [
            "What is the primary purpose of {}?",
            "Which of the following best describes {}?",
            "What are the key components of {}?",
            "When would you typically use {}?"
        ]
    elif difficulty == "intermediate":
        question_templates = [
            "How does {} differ from traditional approaches?",
            "What are the main advantages and limitations of {}?",
            "In what scenarios would {} be most effective?",
            "What are the critical implementation considerations for {}?"
        ]
    else:  # advanced
        question_templates = [
            "What are the theoretical foundations underlying {}?",
            "How would you optimize {} for large-scale applications?",
            "What are the cutting-edge research directions in {}?",
            "How does {} relate to other advanced techniques in the field?"
        ]
    
    # Generate 8-12 questions
    num_questions = random.randint(8, 12)
    used_topics = random.sample(topics * 3, min(len(topics * 3), num_questions))  # Allow topic reuse
    
    for i, topic in enumerate(used_topics[:num_questions]):
        question_id = f"Q{i+1}"
        template = random.choice(question_templates)
        
        question = {
            "id": question_id,
            "stem": template.format(topic),
            "options": [
                {"id": "A", "text": f"Option A about {topic}"},
                {"id": "B", "text": f"Option B about {topic}"},
                {"id": "C", "text": f"Option C about {topic}"},
                {"id": "D", "text": f"Option D about {topic}"}
            ],
            "correct_option_ids": random.choice([["A"], ["B"], ["C"], ["D"], ["A", "B"], ["B", "C"], ["A", "C"]]),
            "rationale": f"The correct answer relates to the fundamental concepts of {topic} as discussed in {doc_title}."
        }
        questions.append(question)
    
    return questions

def generate_quiz_attempt(quiz_id: str, doc_id: str, questions: List[Dict[str, Any]], 
                         base_score: float, variance: float, timestamp: str) -> Dict[str, Any]:
    """Generate a realistic quiz attempt with answers and feedback."""
    
    # Generate score with some variance
    score = max(0, min(100, base_score + random.gauss(0, variance)))
    
    # Generate answers
    answers = []
    per_question_feedback = []
    
    for question in questions:
        correct_ids = question["correct_option_ids"]
        
        # Simulate answer based on score (higher score = more likely correct)
        if random.random() < (score / 100) * 0.8 + 0.1:  # 10-90% chance based on score
            # Correct answer (or partially correct for multi-select)
            if len(correct_ids) > 1 and random.random() < 0.3:
                # Sometimes give partially correct answer
                selected_ids = random.sample(correct_ids, random.randint(1, len(correct_ids)))
            else:
                selected_ids = correct_ids.copy()
        else:
            # Incorrect answer
            all_options = [opt["id"] for opt in question["options"]]
            incorrect_options = [opt for opt in all_options if opt not in correct_ids]
            if incorrect_options:
                selected_ids = [random.choice(incorrect_options)]
            else:
                selected_ids = [random.choice(all_options)]
        
        answers.append({
            "question_id": question["id"],
            "option_ids": selected_ids
        })
        
        # Generate feedback for this question
        options_feedback = []
        for option in question["options"]:
            is_selected = option["id"] in selected_ids
            is_correct = option["id"] in correct_ids
            options_feedback.append({
                "id": option["id"],
                "text": option["text"],
                "selected": is_selected,
                "correct": is_correct
            })
        
        per_question_feedback.append({
            "id": question["id"],
            "correct_option_ids": correct_ids,
            "rationale": question["rationale"],
            "options": options_feedback
        })
    
    return {
        "quiz_id": quiz_id,
        "doc_id": doc_id,
        "score": round(score, 1),
        "answers_json": json.dumps({"answers": answers}),
        "feedback_json": json.dumps({
            "score": round(score, 1),
            "per_question": per_question_feedback
        }),
        "created_at": timestamp
    }

def populate_demo_data(days_back: int = 90, clear_existing: bool = True) -> None:
    """Populate the database with demo data spanning the specified number of days."""
    
    db_path = get_db_path()
    print(f"Using database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    try:
        ensure_schema(conn)
        
        if clear_existing:
            print("Clearing existing demo data...")
            # Keep existing data but clear our demo data (identified by specific patterns)
            conn.execute("DELETE FROM quiz_attempts WHERE doc_id LIKE 'demo_%'")
            conn.execute("DELETE FROM quizzes WHERE doc_id LIKE 'demo_%'")
            conn.execute("DELETE FROM documents WHERE path LIKE 'demo_path_%'")
            conn.execute("DELETE FROM gaps")  # Clear all gaps for fresh start
            conn.commit()
        
        # Insert documents
        print("Creating demo documents...")
        doc_ids = []
        start_date = datetime.now() - timedelta(days=days_back)
        
        for i, doc_data in enumerate(DEMO_DOCUMENTS):
            doc_id = f"demo_doc_{i+1:02d}"
            doc_ids.append(doc_id)
            
            # Spread document creation over time
            created_at = start_date + timedelta(days=i * (days_back // len(DEMO_DOCUMENTS)))
            
            # Insert into documents table with auto-incrementing integer id
            # The doc_id we'll use in quiz_attempts is the string format
            conn.execute("""
                INSERT INTO documents (title, path, created_at)
                VALUES (?, ?, ?)
            """, (doc_data["title"], f"demo_path_{doc_id}.pdf", created_at.isoformat()))
        
        conn.commit()
        print(f"Created {len(doc_ids)} demo documents")
        
        # Insert knowledge gaps
        print("Adding knowledge gaps...")
        gap_sample = random.sample(KNOWLEDGE_GAPS, min(6, len(KNOWLEDGE_GAPS)))
        for gap in gap_sample:
            conn.execute("""
                INSERT INTO gaps (topic, note) VALUES (?, ?)
            """, (gap["topic"], gap["note"]))
        conn.commit()
        
        # Generate quizzes and attempts
        print("Generating quizzes and attempts...")
        total_attempts = 0
        
        for doc_idx, (doc_id, doc_data) in enumerate(zip(doc_ids, DEMO_DOCUMENTS)):
            # Create 2-4 quizzes per document
            num_quizzes = random.randint(2, 4)
            
            for quiz_idx in range(num_quizzes):
                quiz_id = str(uuid.uuid4())
                
                # Generate quiz questions
                questions = generate_quiz_questions(
                    doc_data["title"], 
                    doc_data["topics"], 
                    doc_data["difficulty"]
                )
                
                # Quiz creation time (after document creation)
                doc_created = start_date + timedelta(days=doc_idx * (days_back // len(DEMO_DOCUMENTS)))
                quiz_created = doc_created + timedelta(days=random.randint(1, 7))
                
                # Insert quiz
                quiz_spec = {
                    "quiz_id": quiz_id,
                    "doc_id": doc_id,
                    "questions": questions
                }
                
                conn.execute("""
                    INSERT INTO quizzes (id, doc_id, spec_json, created_at)
                    VALUES (?, ?, ?, ?)
                """, (quiz_id, doc_id, json.dumps(quiz_spec), quiz_created.isoformat()))
                
                # Generate multiple attempts for this quiz (showing progression)
                num_attempts = random.randint(1, 5)
                
                # Calculate progression: start lower, improve over time
                difficulty_multiplier = {"beginner": 1.0, "intermediate": 0.85, "advanced": 0.7}[doc_data["difficulty"]]
                base_score = 45 + (doc_idx * 5)  # Gradual improvement across documents
                base_score *= difficulty_multiplier
                
                for attempt_idx in range(num_attempts):
                    # Progressive improvement within same quiz
                    attempt_score = base_score + (attempt_idx * 8) + random.gauss(0, 10)
                    attempt_score = max(10, min(100, attempt_score))  # Clamp to reasonable range
                    
                    # Attempt time (spread over days/weeks after quiz creation)
                    attempt_time = quiz_created + timedelta(
                        days=attempt_idx * random.randint(1, 7),
                        hours=random.randint(8, 20),
                        minutes=random.randint(0, 59)
                    )
                    
                    # Don't create attempts in the future
                    if attempt_time > datetime.now():
                        continue
                    
                    attempt_data = generate_quiz_attempt(
                        quiz_id, doc_id, questions, attempt_score, 8, attempt_time.isoformat()
                    )
                    
                    conn.execute("""
                        INSERT INTO quiz_attempts 
                        (quiz_id, doc_id, score, answers_json, feedback_json, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        attempt_data["quiz_id"],
                        attempt_data["doc_id"],
                        attempt_data["score"],
                        attempt_data["answers_json"],
                        attempt_data["feedback_json"],
                        attempt_data["created_at"]
                    ))
                    
                    total_attempts += 1
        
        conn.commit()
        print(f"Created {total_attempts} quiz attempts showing progression over time")
        
        # Generate additional recent activity for streak demonstration
        print("Adding recent activity for streak...")
        recent_docs = random.sample(doc_ids, min(3, len(doc_ids)))
        
        for days_ago in range(7, 0, -1):  # Last 7 days
            if random.random() < 0.7:  # 70% chance of activity each day
                doc_id = random.choice(recent_docs)
                
                # Get a quiz for this document
                quiz_rows = conn.execute("""
                    SELECT id FROM quizzes WHERE doc_id = ? LIMIT 1
                """, (doc_id,)).fetchall()
                
                if quiz_rows:
                    quiz_id = quiz_rows[0][0]
                    
                    # Get quiz questions
                    quiz_spec = json.loads(conn.execute("""
                        SELECT spec_json FROM quizzes WHERE id = ?
                    """, (quiz_id,)).fetchone()[0])
                    
                    # Recent scores tend to be higher (showing improvement)
                    recent_score = 70 + random.gauss(15, 10)
                    recent_score = max(40, min(100, recent_score))
                    
                    attempt_time = datetime.now() - timedelta(
                        days=days_ago,
                        hours=random.randint(9, 21),
                        minutes=random.randint(0, 59)
                    )
                    
                    attempt_data = generate_quiz_attempt(
                        quiz_id, doc_id, quiz_spec["questions"], 
                        recent_score, 5, attempt_time.isoformat()
                    )
                    
                    conn.execute("""
                        INSERT INTO quiz_attempts 
                        (quiz_id, doc_id, score, answers_json, feedback_json, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        attempt_data["quiz_id"],
                        attempt_data["doc_id"],
                        attempt_data["score"],
                        attempt_data["answers_json"],
                        attempt_data["feedback_json"],
                        attempt_data["created_at"]
                    ))
                    
                    total_attempts += 1
        
        conn.commit()
        
        # Print summary
        print("\n=== DEMO DATA SUMMARY ===")
        doc_count = conn.execute("SELECT COUNT(*) FROM documents WHERE path LIKE 'demo_path_%'").fetchone()[0]
        quiz_count = conn.execute("SELECT COUNT(*) FROM quizzes WHERE doc_id LIKE 'demo_%'").fetchone()[0]
        attempt_count = conn.execute("SELECT COUNT(*) FROM quiz_attempts WHERE doc_id LIKE 'demo_%'").fetchone()[0]
        gap_count = conn.execute("SELECT COUNT(*) FROM gaps").fetchone()[0]
        
        avg_score = conn.execute("""
            SELECT AVG(score) FROM quiz_attempts WHERE doc_id LIKE 'demo_%'
        """).fetchone()[0]
        
        latest_scores = conn.execute("""
            SELECT score FROM quiz_attempts WHERE doc_id LIKE 'demo_%'
            ORDER BY created_at DESC LIMIT 10
        """).fetchall()
        
        print(f"Documents: {doc_count}")
        print(f"Quizzes: {quiz_count}")
        print(f"Quiz Attempts: {attempt_count}")
        print(f"Knowledge Gaps: {gap_count}")
        print(f"Average Score: {avg_score:.1f}%")
        if latest_scores:
            recent_avg = sum(score[0] for score in latest_scores) / len(latest_scores)
            print(f"Recent Average (last 10): {recent_avg:.1f}%")
        
        print(f"\nDemo data successfully populated!")
        print(f"Database location: {db_path}")
        print(f"Time span: {days_back} days")
        print(f"The dashboard should now show progression graphs, streaks, and learning analytics.")
        
    finally:
        conn.close()

def main():
    """Main function to run the demo data population."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate demo data for dashboard progression")
    parser.add_argument("--days", type=int, default=90, 
                       help="Number of days back to generate data for (default: 90)")
    parser.add_argument("--keep-existing", action="store_true",
                       help="Keep existing data instead of clearing it")
    
    args = parser.parse_args()
    
    print("🚀 Populating Demo Data for Dashboard Progression")
    print("=" * 50)
    
    populate_demo_data(
        days_back=args.days,
        clear_existing=not args.keep_existing
    )

if __name__ == "__main__":
    main()
