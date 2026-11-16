import json

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.models import Answer, EnhancedInterviewReport, InterviewSession, Question, User
from app.routes.analytics import router as analytics_router
from app.routes.enhanced_report import router as enhanced_report_router
from app.routes.interview import router as interview_router
from app.services import company_rag_service
from app.services import ai_service as ai_service_module
from app.services.ai_service import ai_service
from app.services.interview_service import InterviewService
from app.services.multi_agent_service import PerformanceAgent
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
def api_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with test_session() as session:
        user = User(name="Interview Tester", email="interview-tester@example.com", password="hashed")
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

    def override_get_db():
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    def override_current_user():
        with test_session() as session:
            return session.query(User).filter(User.id == user_id).one()

    app = FastAPI()
    app.include_router(interview_router)
    app.include_router(analytics_router)
    app.include_router(enhanced_report_router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def valid_question(**overrides):
    payload = {
        "question": "How does dependency injection improve testability in Spring Boot?",
        "topic": "Spring Boot",
        "category": "Technical",
        "difficulty": "MEDIUM",
        "context": "",
        "evaluation_criteria": ["Explains inversion of control", "Gives a relevant example"],
        "company_specific": False,
    }
    return {**payload, **overrides}


@pytest.mark.parametrize(
    ("company", "role", "skills"),
    [
        ("Amazon", "Java Developer", ["Java", "Spring Boot", "SQL"]),
        ("Google", "Python Developer", ["Python", "Algorithms"]),
        ("TCS", "Full Stack Developer", ["React", "REST APIs"]),
    ],
)
def test_company_question_prompt_uses_selected_configuration(monkeypatch, company, role, skills):
    monkeypatch.setattr(company_rag_service, "retrieve_company_context", lambda *args, **kwargs: "")
    prompts = []

    def fake_chat(client, model, prompt, max_tokens):
        assert hasattr(client, "chat")
        prompts.append(prompt)
        return json.dumps(valid_question())

    monkeypatch.setattr(company_rag_service, "_chat", fake_chat)
    result = company_rag_service.generate_company_questions(
        company=company,
        role=role,
        experience="Fresher",
        skills=skills,
        resume_text=None,
        job_description=None,
        question_types=["Technical"],
        difficulty="MEDIUM",
        interview_round="Technical",
        previous_questions=["Explain a different concept."],
        question_number=3,
        question_count=5,
        interview_duration_minutes=30,
    )

    assert result["questions"][0]["question"] == valid_question()["question"]
    assert company in prompts[0]
    assert role in prompts[0]
    assert ", ".join(skills) in prompts[0]
    assert "Fresher" in prompts[0]
    assert "MEDIUM" in prompts[0]
    assert "QUESTION POSITION: 3 of 5" in prompts[0]
    assert "30 minutes" in prompts[0]
    assert "Explain a different concept." in prompts[0]
    assert result["questions"][0]["evaluation_criteria"]


def test_company_question_works_without_job_description(monkeypatch):
    monkeypatch.setattr(company_rag_service, "retrieve_company_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(
        company_rag_service,
        "_chat",
        lambda *args, **kwargs: json.dumps(valid_question()),
    )

    result = company_rag_service.generate_company_questions(
        company="Amazon",
        role="Java Developer",
        experience="Fresher",
        skills=["Java"],
        resume_text=None,
        job_description=None,
    )

    assert result["questions"][0]["question"]
    assert result["questions"][0]["company_specific"] is False


def test_generic_question_response_has_compatible_ids_and_nonempty_text(api_client, monkeypatch):
    session = api_client.post(
        "/interview/start",
        json={
            "interview_type": "TECHNICAL",
            "category": "Java",
            "question_count": 2,
        },
    ).json()
    monkeypatch.setattr(
        ai_service,
        "generate_interview_question",
        lambda **kwargs: "How does Java manage memory and garbage collection?",
    )

    generated = api_client.post(f"/interview/next-question/{session['id']}", json={})
    assert generated.status_code == 200
    question = generated.json()
    assert question["id"] == question["question_id"]
    assert question["question_text"] == question["question"]
    assert question["question_text"].strip()

    stored = api_client.get(f"/interview/questions/{session['id']}")
    assert stored.status_code == 200
    assert stored.json()[0]["question_text"] == question["question_text"]
    assert stored.json()[0]["question_id"] == question["id"]


def test_empty_saved_question_is_regenerated_without_creating_a_duplicate(db, monkeypatch):
    session = InterviewService.start_session(
        user_id=1,
        interview_type="TECHNICAL",
        db=db,
        session_metadata={"question_count": 2},
    )
    saved = Question(
        session_id=session.id,
        question_text="",
        category="Java",
        difficulty="MEDIUM",
        question_type="TECHNICAL",
    )
    db.add(saved)
    db.commit()
    saved_id = saved.id
    monkeypatch.setattr(
        ai_service,
        "generate_interview_question",
        lambda **kwargs: "How does Java manage memory and garbage collection?",
    )

    question = InterviewService.generate_question(
        session_id=session.id,
        category="Java",
        question_number=1,
        db=db,
    )

    assert question.id == saved_id
    assert question.question_text.strip()
    assert db.query(Question).filter(Question.session_id == session.id).count() == 1


def test_empty_generated_question_is_rejected_before_it_is_saved(db, monkeypatch):
    session = InterviewService.start_session(
        user_id=1,
        interview_type="TECHNICAL",
        db=db,
        session_metadata={"question_count": 1},
    )
    monkeypatch.setattr(ai_service, "generate_interview_question", lambda **kwargs: " ")

    with pytest.raises(HTTPException) as error:
        InterviewService.generate_question(
            session_id=session.id,
            category="Java",
            db=db,
        )

    assert error.value.status_code == 502
    assert db.query(Question).filter(Question.session_id == session.id).count() == 0


def test_generic_ai_generation_retries_empty_content_and_parses_fenced_json(monkeypatch):
    responses = iter([
        "",
        '```json\n{"question":"How does Java garbage collection reclaim unused objects?"}\n```',
    ])
    calls = []

    def fake_chat(*args, **kwargs):
        calls.append(True)
        return next(responses)

    monkeypatch.setattr(ai_service_module, "_chat", fake_chat)
    question = ai_service.generate_interview_question(category="Java")

    assert question == "How does Java garbage collection reclaim unused objects?"
    assert len(calls) == 2


def test_groq_missing_key_is_reported_without_request():
    ai_service_module.get_groq_client.cache_clear()
    original_key = ai_service_module.settings.GROQ_API_KEY
    ai_service_module.settings.GROQ_API_KEY = ""
    try:
        with pytest.raises(HTTPException) as error:
            ai_service_module.get_groq_client()
        raised_error = error.value
    finally:
        ai_service_module.settings.GROQ_API_KEY = original_key
        ai_service_module.get_groq_client.cache_clear()

    assert raised_error.status_code == 503
    assert "GROQ_API_KEY" in raised_error.detail


def test_invalid_or_placeholder_generation_retries_then_fails(monkeypatch):
    monkeypatch.setattr(company_rag_service, "retrieve_company_context", lambda *args, **kwargs: "")
    responses = iter([
        json.dumps(valid_question(question="Technical question for Amazon role")),
        "not json",
    ])
    monkeypatch.setattr(company_rag_service, "_chat", lambda *args, **kwargs: next(responses))

    with pytest.raises(RuntimeError, match="valid interview question"):
        company_rag_service.generate_company_questions(
            company="Amazon",
            role="Java Developer",
            experience="Fresher",
            skills=["Java"],
            resume_text=None,
            job_description=None,
        )


def test_generation_failure_does_not_save_a_placeholder_question(db, monkeypatch):
    session = InterviewService.start_session(
        user_id=1,
        interview_type="TECHNICAL",
        db=db,
        session_metadata={
            "company": "Amazon",
            "company_mode": True,
            "question_count": 5,
        },
    )
    monkeypatch.setattr(
        "app.services.interview_service.generate_company_questions",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("model unavailable")),
    )

    with pytest.raises(RuntimeError, match="Unable to generate a valid"):
        InterviewService.generate_question(
            session_id=session.id,
            category="Technical",
            difficulty="MEDIUM",
            db=db,
        )

    assert db.query(Question).filter(Question.session_id == session.id).count() == 0


def test_question_metadata_skip_and_answer_evaluation_are_saved(db, monkeypatch):
    session = InterviewService.start_session(
        user_id=1,
        interview_type="TECHNICAL",
        db=db,
        session_metadata={
            "company": "Amazon",
            "company_mode": True,
            "role": "Java Developer",
            "question_count": 2,
            "question_details": {},
        },
    )
    monkeypatch.setattr(
        "app.services.interview_service.generate_company_questions",
        lambda **kwargs: {"questions": [valid_question()]},
    )

    first = InterviewService.generate_question(session.id, "Technical", db=db)
    skipped = InterviewService.generate_question(session.id, "Technical", db=db)
    assert first.question_number == 1
    assert skipped.question_number == 2
    assert first.topic == "Spring Boot"
    with pytest.raises(HTTPException) as limit_error:
        InterviewService.generate_question(session.id, "Technical", db=db)
    assert limit_error.value.status_code == 409

    evaluation_calls = []
    def fake_evaluation(**kwargs):
        evaluation_calls.append(kwargs)
        return {
            "score": 8.0,
            "technical_accuracy": 8.0,
            "completeness": 8.0,
            "clarity": 8.0,
            "communication_score": 8.0,
            "feedback": "Correct explanation with a relevant example.",
            "strengths": "Clear understanding.",
            "improvements": "Discuss framework lifecycle.",
            "ideal_answer": "Dependency injection supplies dependencies externally.",
        }
    monkeypatch.setattr(
        ai_service,
        "evaluate_answer",
        fake_evaluation,
    )
    answer = InterviewService.submit_answer(
        first.id,
        "Spring injects collaborators through its container.",
        db=db,
    )
    assert answer.score == 8.0
    assert answer.evaluation_metadata["feedback"]
    assert evaluation_calls[0]["evaluation_criteria"] == valid_question()["evaluation_criteria"]


def test_empty_answer_is_rejected_without_evaluation(db, monkeypatch):
    session = InterviewSession(user_id=1, interview_type="TECHNICAL", session_metadata={})
    db.add(session)
    db.commit()
    question = Question(
        session_id=session.id,
        question_text="Explain dependency injection in Spring Boot.",
        category="Technical",
        difficulty="MEDIUM",
        question_type="TECHNICAL",
    )
    db.add(question)
    db.commit()
    monkeypatch.setattr(
        ai_service,
        "evaluate_answer",
        lambda **kwargs: pytest.fail("Empty answers must not be evaluated."),
    )

    with pytest.raises(HTTPException) as error:
        InterviewService.submit_answer(question.id, "       ", db=db)

    assert error.value.status_code == 422
    assert db.query(Answer).count() == 0


def test_invalid_ai_evaluation_returns_error_instead_of_fixed_score(monkeypatch):
    monkeypatch.setattr(ai_service_module, "_chat", lambda *args, **kwargs: "not json")

    with pytest.raises(HTTPException) as error:
        ai_service.evaluate_answer(
            question="Explain dependency injection in Spring Boot.",
            user_answer="Spring injects collaborators through its container.",
            category="Technical",
        )

    assert error.value.status_code == 502


def test_report_analysis_uses_initialized_client_and_real_model_result(monkeypatch):
    responses = []

    def fake_chat(client, model, prompt, max_tokens):
        assert hasattr(client, "chat")
        responses.append(prompt)
        return json.dumps({
            "overall_score": 81,
            "technical_score": 84,
            "communication_score": 78,
            "hiring_probability": 70,
            "hiring_recommendation": "YES",
            "skill_matrix": {"Java": 84},
            "radar_chart_data": [],
            "strengths": ["Explained the concept clearly."],
            "weaknesses": [],
            "topics_to_improve": [],
            "learning_recommendations": [],
            "ai_summary": "The answer demonstrated a good understanding.",
            "interview_readiness": 81,
        })

    monkeypatch.setattr("app.services.multi_agent_service._chat", fake_chat)
    result = PerformanceAgent().run(
        answers_data=[{"question": "How does dependency injection work?", "answer": "It supplies collaborators.", "score": 8}],
        interview_type="TECHNICAL",
        resume_context="",
        jd_context="",
    )

    assert result["overall_score"] == 81
    assert "It supplies collaborators." in responses[0]


def test_end_session_without_answers_has_no_fabricated_score(db):
    session = InterviewSession(user_id=1, interview_type="TECHNICAL", session_metadata={})
    db.add(session)
    db.commit()
    db.add(Question(
        session_id=session.id,
        question_text="Explain dependency injection in Spring Boot.",
        category="Technical",
        difficulty="MEDIUM",
        question_type="TECHNICAL",
    ))
    db.commit()

    ended = InterviewService.end_session(session.id, db=db)

    assert ended.overall_score is None
    assert ended.total_questions == 1


def test_report_without_answers_does_not_invent_scores(db):
    session = InterviewSession(user_id=1, interview_type="TECHNICAL", session_metadata={})
    db.add(session)
    db.commit()

    report = generate_enhanced_report(session.id, session.user_id, db)

    assert report.overall_score is None
    assert report.technical_score is None
    assert report.confidence_score is None
    assert report.hiring_recommendation == "NOT_EVALUATED"
    assert "No answers were evaluated" in report.ai_summary


def test_company_interview_api_persists_config_generates_evaluates_and_ends(
    api_client, monkeypatch
):
    start = api_client.post(
        "/interview/start",
        json={
            "interview_type": "TECHNICAL",
            "category": "Full Stack",
            "difficulty": "MEDIUM",
            "company": "Amazon",
            "role": "Java Developer",
            "experience": "Fresher",
            "skills": ["Java", "Spring Boot", "SQL"],
            "job_description": None,
            "interview_round": "Technical",
            "question_count": 1,
            "interview_duration_minutes": 30,
            "session_metadata": {"company_mode": True, "monitoring_enabled": True},
        },
    )
    assert start.status_code == 200
    session = start.json()
    session_id = session["id"]
    assert session["session_metadata"]["role"] == "Java Developer"
    assert session["session_metadata"]["monitoring_enabled"] is False

    monkeypatch.setattr(
        "app.services.interview_service.generate_company_questions",
        lambda **kwargs: {"questions": [valid_question()]},
    )
    generated = api_client.post(
        f"/interview/generate-question/{session_id}",
        json={"category": "Amazon Interview", "difficulty": "HARD"},
    )
    assert generated.status_code == 200
    question = generated.json()
    assert question["question_text"] == valid_question()["question"]
    assert question["category"] == "Technical"
    assert question["difficulty"] == "MEDIUM"
    assert question["question_number"] == 1
    assert question["evaluation_criteria"] == valid_question()["evaluation_criteria"]

    questions = api_client.get(f"/interview/questions/{session_id}")
    assert questions.status_code == 200
    assert questions.json()[0]["topic"] == "Spring Boot"

    monkeypatch.setattr(
        ai_service,
        "evaluate_answer",
        lambda **kwargs: {
            "score": 8.0,
            "technical_accuracy": 8.0,
            "completeness": 8.0,
            "clarity": 8.0,
            "communication_score": 8.0,
            "feedback": "Correct explanation.",
            "strengths": "Clear.",
            "improvements": "Add an example.",
            "ideal_answer": "The container supplies collaborators.",
        },
    )
    submitted = api_client.post(
        "/interview/submit-answer",
        json={"question_id": question["id"], "user_answer": "Spring injects collaborators through its container."},
    )
    assert submitted.status_code == 200
    assert submitted.json()["score"] == 8.0

    ended = api_client.post(f"/interview/end/{session_id}")
    assert ended.status_code == 200
    assert ended.json()["total_questions"] == 1
    assert ended.json()["overall_score"] == 8.0


def test_generation_failure_is_an_explicit_api_error(api_client, monkeypatch):
    session = api_client.post(
        "/interview/start",
        json={
            "interview_type": "TECHNICAL",
            "difficulty": "MEDIUM",
            "company": "Amazon",
            "session_metadata": {"company_mode": True},
        },
    ).json()
    monkeypatch.setattr(
        "app.services.interview_service.generate_company_questions",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("model unavailable")),
    )

    response = api_client.post(
        f"/interview/generate-question/{session['id']}",
        json={"category": "Technical", "difficulty": "MEDIUM"},
    )

    assert response.status_code == 502
    assert "Unable to generate a valid" in response.json()["detail"]
    assert api_client.get(f"/interview/questions/{session['id']}").json() == []


def test_five_question_progression_submit_skip_retry_report_and_history(api_client, monkeypatch):
    session = api_client.post(
        "/interview/start",
        json={
            "interview_type": "TECHNICAL",
            "category": "Java",
            "difficulty": "MEDIUM",
            "company": "Amazon",
            "role": "Java Developer",
            "skills": ["Java", "Spring Boot"],
            "question_count": 5,
            "session_metadata": {"company_mode": True},
        },
    ).json()
    session_id = session["id"]

    def generate_question(**kwargs):
        number = kwargs["question_number"]
        return {
            "questions": [valid_question(
                question=f"Question {number}: Explain a Java design decision using a practical production example?",
                topic=f"Java topic {number}",
            )],
        }

    monkeypatch.setattr(
        "app.services.interview_service.generate_company_questions",
        generate_question,
    )
    monkeypatch.setattr(
        ai_service,
        "evaluate_answer",
        lambda **kwargs: {
            "score": 8.0,
            "technical_accuracy": 8.0,
            "completeness": 8.0,
            "clarity": 8.0,
            "communication_score": 8.0,
            "feedback": "A relevant answer.",
            "strengths": "Clear explanation.",
            "improvements": "Add trade-offs.",
            "ideal_answer": "A concise model response.",
        },
    )

    first = api_client.post(f"/interview/next-question/{session_id}", json={})
    assert first.status_code == 200
    current = first.json()
    assert current["question_number"] == 1
    assert current["question"] == current["question_text"]

    def submit_current(question):
        response = api_client.post(
            "/interview/submit-answer",
            json={
                "question_id": question["id"],
                "user_answer": f"My detailed answer for question {question['question_number']}.",
            },
        )
        assert response.status_code == 200
        return response.json()

    first_answer = submit_current(current)
    duplicate_answer = api_client.post(
        "/interview/submit-answer",
        json={
            "question_id": current["id"],
            "user_answer": f"My detailed answer for question {current['question_number']}.",
        },
    )
    assert duplicate_answer.status_code == 200
    assert duplicate_answer.json()["id"] == first_answer["id"]
    duplicate_with_changed_text = api_client.post(
        "/interview/submit-answer",
        json={"question_id": current["id"], "user_answer": "A different answer for the same question."},
    )
    assert duplicate_with_changed_text.status_code == 409
    second = api_client.post(
        f"/interview/next-question/{session_id}",
        json={"current_question_id": current["id"], "action": "answered"},
    ).json()
    assert second["question_number"] == 2
    assert "Question 2:" in second["question"]
    retry_second = api_client.post(
        f"/interview/next-question/{session_id}",
        json={"current_question_id": current["id"], "action": "answered"},
    ).json()
    assert retry_second["id"] == second["id"]
    assert retry_second["question_number"] == 2

    submit_current(second)
    third = api_client.post(
        f"/interview/next-question/{session_id}",
        json={"current_question_id": second["id"], "action": "answered"},
    ).json()
    assert third["question_number"] == 3

    skipped = api_client.post(
        f"/interview/next-question/{session_id}",
        json={"current_question_id": third["id"], "action": "skip"},
    )
    assert skipped.status_code == 200
    fourth = skipped.json()
    assert fourth["question_number"] == 4
    assert "Question 4:" in fourth["question"]

    submit_current(fourth)
    fifth = api_client.post(
        f"/interview/next-question/{session_id}",
        json={"current_question_id": fourth["id"], "action": "answered"},
    ).json()
    assert fifth["question_number"] == 5
    assert "Question 5:" in fifth["question"]
    submit_current(fifth)

    questions = api_client.get(f"/interview/questions/{session_id}").json()
    assert [item["question_number"] for item in questions] == [1, 2, 3, 4, 5]
    assert len({item["id"] for item in questions}) == 5
    assert [item["is_answered"] for item in questions] == [True, True, False, True, True]
    assert [item["is_skipped"] for item in questions] == [False, False, True, False, False]

    ended = api_client.post(f"/interview/end/{session_id}")
    assert ended.status_code == 200
    assert ended.json()["status"] == "COMPLETED"
    assert ended.json()["overall_score"] == 8.0
    assert ended.json()["total_questions"] == 5

    def create_report(session_id, user_id, db):
        report = EnhancedInterviewReport(
            session_id=session_id,
            user_id=user_id,
            overall_score=80,
            technical_score=82,
            communication_score=78,
            confidence_score=None,
            hiring_probability=70,
            hiring_recommendation="YES",
            skill_matrix={"Java": 82},
            radar_chart_data=[],
            strengths=["Clear explanations"],
            weaknesses=["Discuss trade-offs"],
            topics_to_improve=["Spring Boot"],
            learning_recommendations=["Practice design questions"],
            ai_summary="Good technical performance.",
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    monkeypatch.setattr("app.routes.enhanced_report.generate_enhanced_report", create_report)
    report = api_client.post(f"/report/generate/{session_id}")
    assert report.status_code == 200
    assert len(report.json()["question_feedback"]) == 4

    history = api_client.get("/analytics/history")
    assert history.status_code == 200
    assert history.json()["interviews"][0]["id"] == session_id
    assert history.json()["interviews"][0]["status"] == "COMPLETED"


def test_next_question_rejects_missing_session_and_question(api_client):
    missing_session = api_client.post(
        "/interview/next-question/999999",
        json={"current_question_id": None, "action": "start"},
    )
    assert missing_session.status_code == 404

    session = api_client.post(
        "/interview/start",
        json={"interview_type": "TECHNICAL", "category": "Java"},
    ).json()
    invalid_question = api_client.post(
        f"/interview/next-question/{session['id']}",
        json={"current_question_id": 999999, "action": "answered"},
    )
    assert invalid_question.status_code == 404
