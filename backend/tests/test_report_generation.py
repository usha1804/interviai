import pytest
from types import SimpleNamespace
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.config import settings
from app.models.models import Answer, EnhancedInterviewReport, InterviewSession, Question, User
from app.routes.enhanced_report import router as report_router
from app.services import ai_service as ai_service_module
from app.services.multi_agent_service import PerformanceAgent, coordinator
from app.services.report_prompt_utils import (
    estimate_prompt_tokens,
    prompt_within_limits,
    request_payload_size,
    select_relevant_context,
    split_text_preserving_content,
)
from app.services.report_service import generate_enhanced_report
from app.utils.auth import get_current_user


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def report_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with factory() as session:
        user = User(name="Report Tester", email="report-tester@example.com", password="hash")
        session.add(user)
        session.commit()
        user_id = user.id

    def override_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    def override_user():
        with factory() as session:
            return session.query(User).filter(User.id == user_id).one()

    app = FastAPI()
    app.include_router(report_router)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as client:
        client.app.state.test_session_factory = factory
        client.app.state.test_user_id = user_id
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def valid_analysis(**overrides):
    result = {
        "overall_score": 81,
        "technical_score": 84,
        "communication_score": 78,
        "hiring_probability": 70,
        "hiring_recommendation": "YES",
        "skill_matrix": {"Java": 82},
        "radar_chart_data": [{"subject": "Technical", "score": 84}],
        "strengths": ["Clear explanation"],
        "weaknesses": ["Needs examples"],
        "topics_to_improve": ["Concurrency"],
        "learning_recommendations": ["Practice concurrency scenarios"],
        "ai_summary": "Candidate demonstrates a solid technical foundation.",
    }
    return {**result, **overrides}


def add_session_with_answers(db, user_id=1, answer_text="A detailed answer with implementation trade-offs."):
    session = InterviewSession(user_id=user_id, interview_type="TECHNICAL", session_metadata={})
    db.add(session)
    db.commit()
    question = Question(
        session_id=session.id,
        question_text="How would you design a reliable service?",
        category="System Design",
        difficulty="MEDIUM",
        question_type="TECHNICAL",
    )
    db.add(question)
    db.commit()
    answer = Answer(
        question_id=question.id,
        user_answer=answer_text,
        score=8,
        technical_accuracy=8,
        completeness=7,
        clarity=8,
        communication_score=8,
    )
    db.add(answer)
    db.commit()
    return session


def test_normal_report_generation_and_existing_report_retrieval(report_client, monkeypatch):
    with report_client.app.state.test_session_factory() as db:
        session = add_session_with_answers(db, report_client.app.state.test_user_id)
        session_id = session.id
    monkeypatch.setattr(coordinator, "analyze_full_interview", lambda **kwargs: valid_analysis())
    monkeypatch.setattr(
        "app.services.report_service.retrieve_report_resume_context",
        lambda *args, **kwargs: "Java skills include production service design.",
    )
    monkeypatch.setattr(
        "app.services.report_service.retrieve_report_jd_context",
        lambda *args, **kwargs: "Required skills include Java service development.",
    )

    generated = report_client.post(f"/report/generate/{session_id}")
    regenerated = report_client.post(f"/report/generate/{session_id}")
    fetched = report_client.get(f"/report/{session_id}")

    assert generated.status_code == 200
    assert generated.json()["overall_score"] == 81
    assert regenerated.json()["id"] == generated.json()["id"]
    assert fetched.status_code == 200
    assert fetched.json()["id"] == generated.json()["id"]


def test_report_generation_is_idempotent_and_get_returns_persisted_report(db, monkeypatch):
    session = add_session_with_answers(db)
    analysis_calls = []
    monkeypatch.setattr(
        coordinator,
        "analyze_full_interview",
        lambda **kwargs: analysis_calls.append(kwargs) or valid_analysis(),
    )
    monkeypatch.setattr("app.services.report_service.retrieve_report_resume_context", lambda *args, **kwargs: "Java skills and production services.")
    monkeypatch.setattr("app.services.report_service.retrieve_report_jd_context", lambda *args, **kwargs: "Required skills include Java.")

    first = generate_enhanced_report(session.id, session.user_id, db)
    second = generate_enhanced_report(session.id, session.user_id, db)

    assert first.id == second.id
    assert len(analysis_calls) == 1
    assert len(analysis_calls[0]["answers_data"]) == 1
    assert analysis_calls[0]["answers_data"][0]["question_ids"]


def test_large_interview_and_long_answers_are_batched_without_dropping_text(db, monkeypatch):
    session = InterviewSession(user_id=1, interview_type="TECHNICAL", session_metadata={})
    db.add(session)
    db.commit()
    original_by_question = {}
    for index in range(8):
        question = Question(
            session_id=session.id,
            question_text=f"Question {index}: explain a reliable design decision.",
            category="System Design",
            difficulty="MEDIUM",
            question_type="TECHNICAL",
        )
        db.add(question)
        db.commit()
        answer_text = (f"Evidence {index}. " * 1200) + f"Final marker {index}."
        original_by_question[question.id] = answer_text
        db.add(Answer(
            question_id=question.id,
            user_answer=answer_text,
            score=8,
            technical_accuracy=8,
            completeness=7,
            clarity=8,
            communication_score=8,
        ))
        db.commit()

    received = []

    def fake_analysis(**kwargs):
        assert not db.in_transaction()
        received.append(kwargs)
        return valid_analysis()

    monkeypatch.setattr(coordinator, "analyze_full_interview", fake_analysis)
    monkeypatch.setattr(
        "app.services.report_service.retrieve_report_resume_context",
        lambda *args, **kwargs: "Java skills include production service design.",
    )
    monkeypatch.setattr(
        "app.services.report_service.retrieve_report_jd_context",
        lambda *args, **kwargs: "Required skills include Java service development.",
    )

    report = generate_enhanced_report(session.id, session.user_id, db)

    assert report.overall_score == 81
    assert len(received) > 2  # multiple source batches and a compact summary combination
    assert received[0]["resume_ctx"] and received[0]["jd_ctx"]
    assert all(not call["resume_ctx"] and not call["jd_ctx"] for call in received[1:])
    for call in received:
        prompt = coordinator.performance_agent.build_prompt(
            call["answers_data"],
            call["interview_type"],
            call["resume_ctx"],
            call["jd_ctx"],
        )
        assert prompt_within_limits(prompt, settings.GROQ_MODEL, 2000)
    reconstructed = {question_id: [] for question_id in original_by_question}
    for call in received:
        for item in call["answers_data"]:
            for question_id in item["question_ids"]:
                if question_id in reconstructed:
                    reconstructed[question_id].append(item["answer"])
    for question_id, answer_text in original_by_question.items():
        assert "".join(reconstructed[question_id]) == answer_text


def test_duplicate_qa_and_retrieved_context_are_deduplicated(db, monkeypatch):
    session = InterviewSession(user_id=1, interview_type="TECHNICAL", session_metadata={})
    db.add(session)
    db.commit()
    question_ids = []
    for _ in range(2):
        question = Question(
            session_id=session.id,
            question_text="How does indexing improve database queries?",
            category="SQL",
            difficulty="MEDIUM",
            question_type="TECHNICAL",
        )
        db.add(question)
        db.commit()
        question_ids.append(question.id)
        db.add(Answer(
            question_id=question.id,
            user_answer="An index reduces the rows scanned for a selective query.",
            score=7,
            technical_accuracy=7,
        ))
        db.commit()

    captured = []
    monkeypatch.setattr(coordinator, "analyze_full_interview", lambda **kwargs: captured.append(kwargs) or valid_analysis())
    repeated_context = "Java skills support service delivery. " * 300
    monkeypatch.setattr("app.services.report_service.retrieve_report_resume_context", lambda *args, **kwargs: repeated_context)
    monkeypatch.setattr("app.services.report_service.retrieve_report_jd_context", lambda *args, **kwargs: repeated_context)

    generate_enhanced_report(session.id, session.user_id, db)

    assert len(captured[0]["answers_data"]) == 1
    assert captured[0]["answers_data"][0]["question_ids"] == question_ids
    assert len(captured[0]["resume_ctx"]) <= 1400
    assert len(captured[0]["jd_ctx"]) <= 1400


def test_report_persistence_failure_rolls_back_without_saving_partial_report(db, monkeypatch):
    session = add_session_with_answers(db)
    monkeypatch.setattr(coordinator, "analyze_full_interview", lambda **kwargs: valid_analysis())
    monkeypatch.setattr("app.services.report_service.retrieve_report_resume_context", lambda *args, **kwargs: "")
    monkeypatch.setattr("app.services.report_service.retrieve_report_jd_context", lambda *args, **kwargs: "")
    original_commit = db.commit
    calls = 0

    def fail_report_commit():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("simulated report write failure")
        original_commit()

    monkeypatch.setattr(db, "commit", fail_report_commit)
    with pytest.raises(RuntimeError, match="simulated report write failure"):
        generate_enhanced_report(session.id, session.user_id, db)
    monkeypatch.setattr(db, "commit", original_commit)
    assert db.query(EnhancedInterviewReport).filter_by(session_id=session.id).count() == 0


def test_report_batch_failure_does_not_persist_a_partial_report(db, monkeypatch):
    session = InterviewSession(user_id=1, interview_type="TECHNICAL", session_metadata={})
    db.add(session)
    db.commit()
    for index in range(5):
        question = Question(
            session_id=session.id,
            question_text=f"Question {index}: explain a reliable design decision.",
            category="System Design",
            difficulty="MEDIUM",
            question_type="TECHNICAL",
        )
        db.add(question)
        db.commit()
        db.add(Answer(question_id=question.id, user_answer=("Answer detail. " * 1200), score=8))
        db.commit()
    monkeypatch.setattr("app.services.report_service.retrieve_report_resume_context", lambda *args, **kwargs: "")
    monkeypatch.setattr("app.services.report_service.retrieve_report_jd_context", lambda *args, **kwargs: "")
    calls = []

    def fail_second_batch(**kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            raise HTTPException(status_code=502, detail="Batch generation failed.")
        return valid_analysis()

    monkeypatch.setattr(coordinator, "analyze_full_interview", fail_second_batch)
    with pytest.raises(HTTPException, match="Batch generation failed"):
        generate_enhanced_report(session.id, session.user_id, db)

    assert len(calls) == 2
    assert db.query(EnhancedInterviewReport).filter_by(session_id=session.id).count() == 0


def test_report_request_payload_size_and_text_splitting_are_safe():
    source = ("A full sentence with technical details. " * 5000) + "terminal"
    pieces = split_text_preserving_content(source, 1000)
    assert "".join(pieces) == source
    assert max(map(len, pieces)) <= 1000
    assert estimate_prompt_tokens("Compact test prompt", "openai/gpt-oss-20b") > 0
    assert request_payload_size("model", "hello", 20) < 1000


class GroqStatusError(Exception):
    def __init__(self, status_code):
        super().__init__(f"Groq HTTP {status_code}")
        self.status_code = status_code


class FakeGroqClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, BaseException):
            raise outcome
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=outcome))]
        )


def test_groq_chat_uses_client_sdk_and_returns_cleaned_response():
    client = FakeGroqClient(["  a generated question  "])
    assert ai_service_module._chat(client, "model", "prompt", max_tokens=22) == "a generated question"
    assert client.calls[0]["model"] == "model"
    assert client.calls[0]["max_tokens"] == 22
    assert client.calls[0]["messages"] == [{"role": "user", "content": "prompt"}]


def test_groq_empty_response_and_invalid_client_return_clear_errors():
    with pytest.raises(HTTPException) as empty:
        ai_service_module._chat(FakeGroqClient(["  "]), "model", "prompt")
    assert empty.value.status_code == 502

    with pytest.raises(HTTPException) as invalid:
        ai_service_module._chat(object(), "model", "prompt")
    assert invalid.value.status_code == 500
    assert "initialized Groq client" in invalid.value.detail


def test_groq_429_retries_with_backoff_and_eventually_succeeds(monkeypatch):
    delays = []
    client = FakeGroqClient([GroqStatusError(429), "ok"])
    monkeypatch.setattr(ai_service_module.time, "sleep", delays.append)
    assert ai_service_module._chat(client, "model", "prompt") == "ok"
    assert delays == [0.5]
    assert len(client.calls) == 2


def test_groq_413_and_500_errors_are_handled(monkeypatch):
    monkeypatch.setattr(ai_service_module.time, "sleep", lambda *_: None)
    with pytest.raises(HTTPException) as too_large:
        ai_service_module._chat(FakeGroqClient([GroqStatusError(413)]), "model", "prompt")
    assert too_large.value.status_code == 413

    client = FakeGroqClient([GroqStatusError(500), GroqStatusError(500), GroqStatusError(500)])
    with pytest.raises(HTTPException) as upstream:
        ai_service_module._chat(client, "model", "prompt")
    assert upstream.value.status_code == 502
    assert len(client.calls) == 3


@pytest.mark.parametrize(
    ("exception", "status"),
    [(TimeoutError("timeout"), 504), (ConnectionError("network disconnected"), 503)],
)
def test_groq_network_failures_are_reported(monkeypatch, exception, status):
    monkeypatch.setattr(ai_service_module.time, "sleep", lambda *_: None)
    with pytest.raises(HTTPException) as error:
        ai_service_module._chat(FakeGroqClient([exception]), "model", "prompt")
    assert error.value.status_code == status


@pytest.mark.parametrize("status_code", [401, 403])
def test_groq_authentication_and_permission_errors_are_distinct(status_code):
    with pytest.raises(HTTPException) as error:
        ai_service_module._chat(
            FakeGroqClient([GroqStatusError(status_code)]),
            "model",
            "prompt",
        )
    assert error.value.status_code == 502
    assert "authentication or permission" in error.value.detail.casefold()


def test_performance_agent_rejects_invalid_report_json(monkeypatch):
    monkeypatch.setattr("app.services.multi_agent_service._chat", lambda *args, **kwargs: "not JSON")
    with pytest.raises(HTTPException) as error:
        PerformanceAgent().run(
            answers_data=[{"question_ids": [1], "question": "Q", "answer": "A", "score": 8}],
            interview_type="TECHNICAL",
            resume_context="",
            jd_context="",
        )
    assert error.value.status_code == 502


def test_context_selector_keeps_complete_deduplicated_relevant_sentences():
    context = (
        "Java memory management uses garbage collection. "
        "Unrelated office details are not useful. "
        "Java memory management uses garbage collection."
    )
    selected = select_relevant_context(context, "Java memory management", max_chars=100)
    assert selected == "Java memory management uses garbage collection."
    assert len(selected) <= 100
