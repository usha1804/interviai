from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.models import Answer, InterviewMemory, InterviewSession, Question, User
from app.routes import adaptive as adaptive_route
from app.routes.adaptive import router as adaptive_router
from app.services import adaptive_engine
from app.services import ai_service as ai_service_module
from app.services.ai_service import ai_service
from app.services.adaptive_engine import (
    compute_next_difficulty,
    generate_adaptive_question,
)
from app.utils.auth import get_current_user


@pytest.fixture
def adaptive_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with factory() as db:
        user = User(name="Adaptive Tester", email="adaptive-tester@example.com", password="hash")
        db.add(user)
        db.commit()
        user_id = user.id

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    def override_user():
        with factory() as db:
            return db.query(User).filter(User.id == user_id).one()

    app = FastAPI()
    app.include_router(adaptive_router)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    app.state.session_factory = factory
    app.state.user_id = user_id
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def create_adaptive_session(client, count=5):
    with client.app.state.session_factory() as db:
        session = InterviewSession(
            user_id=client.app.state.user_id,
            interview_type="TECHNICAL",
            status="IN_PROGRESS",
            session_metadata={"question_count": count},
        )
        db.add(session)
        db.commit()
        return session.id


def mock_evaluation(**kwargs):
    return {
        "score": 9.0,
        "technical_accuracy": 9.0,
        "completeness": 8.0,
        "clarity": 9.0,
        "communication_score": 8.0,
        "feedback": "A clear answer with good detail.",
        "strengths": "Logical approach.",
        "improvements": "Discuss edge cases.",
        "ideal_answer": "An answer with trade-offs and edge cases.",
    }


def test_generate_adaptive_question_uses_groq_and_avoids_asked_question(monkeypatch):
    prompts = []
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: None)))

    def fake_chat(groq_client, model, prompt, max_tokens):
        assert groq_client is client
        prompts.append(prompt)
        return "How would you design a rate limiter for a distributed API?"

    monkeypatch.setattr(adaptive_engine, "get_groq_client", lambda: client)
    monkeypatch.setattr(adaptive_engine, "_chat", fake_chat)

    question = generate_adaptive_question(
        category="Backend",
        difficulty="HARD",
        question_type="SYSTEM_DESIGN",
        asked_questions=["Explain a database index."],
        weak_topics=["Caching"],
        strong_topics=["Java"],
        resume_context="Built Java services.",
        company="Example Co",
    )

    assert question.startswith("How would you design")
    assert "HARD" in prompts[0]
    assert "Caching" in prompts[0]
    assert "Explain a database index." in prompts[0]


def test_adaptive_generation_rejects_duplicate_and_unusable_questions(monkeypatch):
    monkeypatch.setattr(adaptive_engine, "get_groq_client", lambda: object())
    monkeypatch.setattr(adaptive_engine, "_chat", lambda *args, **kwargs: "Explain a database index.")
    with pytest.raises(HTTPException) as duplicate:
        generate_adaptive_question(
            category="SQL",
            difficulty="MEDIUM",
            question_type="TECHNICAL",
            asked_questions=["  Explain a database index. "],
            weak_topics=[],
            strong_topics=[],
        )
    assert duplicate.value.status_code == 502

    monkeypatch.setattr(adaptive_engine, "_chat", lambda *args, **kwargs: "short")
    with pytest.raises(HTTPException) as invalid:
        generate_adaptive_question(
            category="SQL",
            difficulty="MEDIUM",
            question_type="TECHNICAL",
            asked_questions=[],
            weak_topics=[],
            strong_topics=[],
        )
    assert invalid.value.status_code == 502


def test_adaptive_next_question_retry_and_submission_are_idempotent(adaptive_client, monkeypatch):
    session_id = create_adaptive_session(adaptive_client)
    monkeypatch.setattr(adaptive_route, "retrieve_resume_context", lambda *args, **kwargs: "Backend service experience.")
    generated = []

    def generate_question(**kwargs):
        text = f"Generated adaptive question {len(generated) + 1}: explain a reliable design choice?"
        generated.append((text, kwargs))
        return text

    monkeypatch.setattr(adaptive_route, "generate_adaptive_question", generate_question)
    monkeypatch.setattr(ai_service, "evaluate_answer", mock_evaluation)

    first_response = adaptive_client.post(
        "/adaptive/next-question",
        json={"session_id": session_id, "category": "Java"},
    )
    assert first_response.status_code == 200
    first = first_response.json()["question"]
    assert first["question_number"] == 1
    assert first["session_id"] == session_id

    retry = adaptive_client.post(
        "/adaptive/next-question",
        json={
            "session_id": session_id,
            "category": "Java",
            "current_question_id": first["id"],
        },
    )
    assert retry.status_code == 200
    assert retry.json()["question"]["id"] == first["id"]
    assert len(generated) == 1

    submitted = adaptive_client.post(
        "/adaptive/submit-answer",
        json={
            "session_id": session_id,
            "question_id": first["id"],
            "user_answer": "My detailed answer explains trade-offs and production behavior.",
        },
    )
    assert submitted.status_code == 200
    repeated_submit = adaptive_client.post(
        "/adaptive/submit-answer",
        json={
            "session_id": session_id,
            "question_id": first["id"],
            "user_answer": "My detailed answer explains trade-offs and production behavior.",
        },
    )
    assert repeated_submit.status_code == 200
    assert repeated_submit.json()["answer_id"] == submitted.json()["answer_id"]

    second_response = adaptive_client.post(
        "/adaptive/next-question",
        json={
            "session_id": session_id,
            "category": "Java",
            "current_question_id": first["id"],
        },
    )
    assert second_response.status_code == 200
    second = second_response.json()["question"]
    assert second["question_number"] == 2
    assert second["difficulty"] == "HARD"
    assert second_response.json()["adaptive_info"]["difficulty_changed"] is True

    retry_after_response_loss = adaptive_client.post(
        "/adaptive/next-question",
        json={
            "session_id": session_id,
            "category": "Java",
            "current_question_id": first["id"],
        },
    )
    assert retry_after_response_loss.json()["question"]["id"] == second["id"]
    assert len(generated) == 2

    with adaptive_client.app.state.session_factory() as db:
        questions = db.query(Question).filter_by(session_id=session_id).order_by(Question.id).all()
        answers = db.query(Answer).join(Question).filter(Question.session_id == session_id).all()
        memory = db.query(InterviewMemory).filter_by(user_id=adaptive_client.app.state.user_id).one()
        assert len(questions) == 2
        assert len(answers) == 1
        assert memory.last_difficulty == "HARD"
        assert len(memory.asked_questions) == 2


def test_adaptive_generation_failure_can_be_retried_without_duplicate_questions(adaptive_client, monkeypatch):
    session_id = create_adaptive_session(adaptive_client)
    monkeypatch.setattr(adaptive_route, "retrieve_resume_context", lambda *args, **kwargs: "")
    attempts = []

    def generate_question(**kwargs):
        attempts.append(True)
        if len(attempts) == 1:
            raise HTTPException(status_code=503, detail="Groq is temporarily unavailable.")
        return "How would you isolate failures in a distributed service?"

    monkeypatch.setattr(adaptive_route, "generate_adaptive_question", generate_question)
    payload = {"session_id": session_id, "category": "Backend"}
    failed = adaptive_client.post("/adaptive/next-question", json=payload)
    retried = adaptive_client.post("/adaptive/next-question", json=payload)

    assert failed.status_code == 503
    assert retried.status_code == 200
    assert retried.json()["question"]["question_number"] == 1
    assert len(attempts) == 2
    with adaptive_client.app.state.session_factory() as db:
        assert db.query(Question).filter_by(session_id=session_id).count() == 1


def test_adaptive_routes_reject_unknown_session_and_wrong_question_owner(adaptive_client):
    missing = adaptive_client.post(
        "/adaptive/next-question",
        json={"session_id": 9999, "category": "Backend"},
    )
    assert missing.status_code == 404

    session_id = create_adaptive_session(adaptive_client)
    unknown_question = adaptive_client.post(
        "/adaptive/submit-answer",
        json={
            "session_id": session_id,
            "question_id": 9999,
            "user_answer": "This answer is long enough to pass validation.",
        },
    )
    assert unknown_question.status_code == 404


def test_adaptive_difficulty_adjusts_after_poor_recent_performance():
    assert compute_next_difficulty([3.0, 3.0], "HARD") == "MEDIUM"
