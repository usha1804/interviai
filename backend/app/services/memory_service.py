"""
Memory service — tracks per-user interview history to avoid repeating questions
and progressively increase difficulty.
"""
from sqlalchemy.orm import Session
from app.models.models import InterviewMemory


def get_or_create(user_id: int, db: Session) -> InterviewMemory:
    mem = db.query(InterviewMemory).filter(InterviewMemory.user_id == user_id).first()
    if not mem:
        mem = InterviewMemory(user_id=user_id)
        db.add(mem)
        db.commit()
        db.refresh(mem)
    return mem


def record_question(user_id: int, question_text: str, db: Session):
    mem = get_or_create(user_id, db)
    asked = list(mem.asked_questions or [])
    if question_text not in asked:
        asked.append(question_text)
        mem.asked_questions = asked[-200:]  # keep last 200
    db.commit()


def record_answer_score(user_id: int, topic: str, score: float, db: Session):
    mem = get_or_create(user_id, db)
    scores = dict(mem.topic_scores or {})
    prev = scores.get(topic, score)
    scores[topic] = round((prev + score) / 2, 2)
    mem.topic_scores = scores

    weak = [t for t, s in scores.items() if s < 5.0]
    strong = [t for t, s in scores.items() if s >= 7.5]
    mem.weak_topics = weak
    mem.strong_topics = strong
    db.commit()


def increment_session(user_id: int, db: Session):
    mem = get_or_create(user_id, db)
    mem.total_sessions = (mem.total_sessions or 0) + 1
    # Auto-escalate difficulty
    if mem.total_sessions >= 10:
        mem.last_difficulty = "HARD"
    elif mem.total_sessions >= 4:
        mem.last_difficulty = "MEDIUM"
    db.commit()


def get_asked_questions(user_id: int, db: Session):
    mem = get_or_create(user_id, db)
    return mem.asked_questions or []


def get_next_difficulty(user_id: int, db: Session) -> str:
    mem = get_or_create(user_id, db)
    return mem.last_difficulty or "MEDIUM"
