import copy
from datetime import datetime

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.models import User, VoiceInterviewSession
from app.routes.voice_interview import router as voice_router
from app.utils.auth import get_current_user


@pytest.fixture
def voice_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with test_session() as db:
        user = User(name="Voice Tester", email="voice-tester@example.com", password="hashed")
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    def override_current_user():
        with test_session() as db:
            return db.query(User).filter(User.id == user_id).one()

    app = FastAPI()
    app.include_router(voice_router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    with TestClient(app) as client:
        yield client, test_session, user_id
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def start_voice(http, monkeypatch):
    monkeypatch.setattr(
        "app.routes.voice_interview.ai_service.generate_interview_question",
        lambda **kwargs: "How do you design a reliable service?",
    )
    return http.post("/voice/start", json={"interview_type": "TECHNICAL", "category": "Technical"})


def test_start_voice_interview_does_not_require_audio(voice_client, monkeypatch):
    http, test_session, _ = voice_client
    response = start_voice(http, monkeypatch)

    assert response.status_code == 200
    assert response.json()["first_question"] == "How do you design a reliable service?"
    assert response.json()["question_number"] == 1
    with test_session() as db:
        session = db.query(VoiceInterviewSession).one()
        assert session.status == "IN_PROGRESS"
        assert session.transcript[0]["role"] == "ai"


def test_missing_audio_is_rejected_only_when_answer_is_submitted(voice_client, monkeypatch):
    http, _, _ = voice_client
    started = start_voice(http, monkeypatch)
    response = http.post(f"/voice/stt/{started.json()['session_id']}")
    assert response.status_code == 400
    assert "record an answer before submitting" in response.json()["detail"].casefold()


@pytest.mark.parametrize(
    ("content", "status", "detail"),
    [
        (b"", 400, "empty"),
        (b"not an audio file", 415, "Unsupported audio format"),
    ],
)
def test_audio_upload_rejects_empty_or_unsupported_audio(voice_client, monkeypatch, content, status, detail):
    http, _, _ = voice_client
    started = start_voice(http, monkeypatch)
    response = http.post(
        f"/voice/stt/{started.json()['session_id']}",
        files={"audio": ("answer.webm", content, "audio/webm")},
    )
    assert response.status_code == status
    assert detail in response.json()["detail"]


def test_five_audio_answers_are_transcribed_evaluated_and_complete(voice_client, monkeypatch):
    http, test_session, _ = voice_client
    monkeypatch.setattr(
        "app.routes.voice_interview.ai_service.generate_interview_question",
        lambda **kwargs: f"Question {len(kwargs.get('previous_topics', [])) + 1}: discuss reliability.",
    )
    monkeypatch.setattr(
        "app.routes.voice_interview.ai_service.evaluate_answer",
        lambda **kwargs: {"score": 8, "feedback": "Clear and relevant."},
    )
    monkeypatch.setattr(
        "app.routes.voice_interview.speech_to_text",
        lambda audio: {"transcript": "I would use monitoring and retries.", "duration_seconds": 4.0},
    )
    started = http.post("/voice/start", json={"interview_type": "TECHNICAL", "category": "Technical"})
    assert started.status_code == 200
    session_id = started.json()["session_id"]
    question_id = started.json()["current_question_id"]

    for question_number in range(1, 6):
        response = http.post(
            f"/voice/stt/{session_id}",
            data={"question_id": question_id},
            files={"audio": ("answer.webm", b"\x1a\x45\xdf\xa3mock", "audio/webm")},
        )
        assert response.status_code == 200, response.text
        assert response.json()["transcript"] == "I would use monitoring and retries."
        assert response.json()["evaluation"]["score"] == 8
        if question_number < 5:
            assert response.json()["next_question"]
            assert response.json()["completed"] is False
            assert response.json()["current_question_id"]
            question_id = response.json()["current_question_id"]
        else:
            assert response.json()["next_question"] is None
            assert response.json()["current_question_id"] is None
            assert response.json()["completed"] is True

    report = http.post(f"/voice/end/{session_id}")
    assert report.status_code == 200, report.text
    assert report.json()["total_turns"] == 5
    report_answers = [turn for turn in report.json()["transcript"] if turn["role"] == "candidate"]
    assert len(report_answers) == 5
    assert all(turn["text"] == "I would use monitoring and retries." for turn in report_answers)
    assert all(turn["evaluation"]["score"] == 8 for turn in report_answers)
    with test_session() as db:
        session = db.query(VoiceInterviewSession).one()
        assert session.status == "COMPLETED"
        assert all(turn.get("evaluation") for turn in session.transcript if turn["role"] == "candidate")


def test_duplicate_question_upload_is_idempotent_and_returns_next_question(voice_client, monkeypatch):
    http, test_session, _ = voice_client
    questions = iter(["Question one: reliability?", "Question two: observability?"])
    monkeypatch.setattr(
        "app.routes.voice_interview.ai_service.generate_interview_question",
        lambda **kwargs: next(questions),
    )
    evaluations = []

    def fake_evaluation(**kwargs):
        evaluations.append(kwargs["user_answer"])
        return {"score": 8, "feedback": "Clear response."}

    monkeypatch.setattr("app.routes.voice_interview.ai_service.evaluate_answer", fake_evaluation)
    transcriptions = []

    def fake_transcription(audio):
        transcriptions.append(audio)
        return {"transcript": "I use health checks and metrics.", "duration_seconds": 4.0}

    monkeypatch.setattr("app.routes.voice_interview.speech_to_text", fake_transcription)
    started = http.post("/voice/start", json={"interview_type": "TECHNICAL", "category": "Technical"})
    session_id = started.json()["session_id"]
    qid = started.json()["current_question_id"]
    upload = {
        "files": {"audio": ("answer.webm", b"\x1a\x45\xdf\xa3mock", "audio/webm")},
        "data": {"question_id": qid},
    }

    first = http.post(f"/voice/stt/{session_id}", **upload)
    assert first.status_code == 200
    assert first.json()["current_question_id"] != qid
    assert first.json()["question_number"] == 2
    replay = http.post(f"/voice/stt/{session_id}", **upload)

    assert replay.status_code == 200, replay.text
    assert replay.json()["already_processed"] is True
    assert replay.json()["answered_question_id"] == qid
    assert replay.json()["question_number"] == 2
    assert replay.json()["current_question_id"] == first.json()["current_question_id"]
    assert len(transcriptions) == 1
    assert len(evaluations) == 1
    with test_session() as db:
        session = db.query(VoiceInterviewSession).one()
        answers = [turn for turn in session.transcript if turn["role"] == "candidate"]
        assert len(answers) == 1
    resumed = http.get(f"/voice/session/{session_id}")
    assert resumed.status_code == 200
    assert resumed.json()["current_question_id"] == first.json()["current_question_id"]
    assert len([turn for turn in resumed.json()["transcript"] if turn["role"] == "candidate"]) == 1


def test_refresh_session_returns_current_question_and_saved_progress(voice_client, monkeypatch):
    http, _, _ = voice_client
    started = start_voice(http, monkeypatch)
    session_id = started.json()["session_id"]
    response = http.get(f"/voice/session/{session_id}")

    assert response.status_code == 200
    assert response.json()["current_question"] == started.json()["first_question"]
    assert response.json()["current_question_id"] == started.json()["current_question_id"]
    assert response.json()["question_number"] == 1
    assert response.json()["transcript"][0]["role"] == "ai"


def test_processing_question_keeps_conflict_guard_without_duplicate_transcription(voice_client, monkeypatch):
    http, test_session, _ = voice_client
    started = start_voice(http, monkeypatch)
    session_id = started.json()["session_id"]
    question_id = started.json()["current_question_id"]
    with test_session() as db:
        session = db.query(VoiceInterviewSession).one()
        transcript = copy.deepcopy(session.transcript)
        transcript[0]["submission_status"] = "processing"
        transcript[0]["submission_started_at"] = datetime.utcnow().isoformat()
        session.transcript = transcript
        db.commit()

    def should_not_transcribe(_audio):
        raise AssertionError("The same question must not be transcribed concurrently.")

    monkeypatch.setattr("app.routes.voice_interview.speech_to_text", should_not_transcribe)
    response = http.post(
        f"/voice/stt/{session_id}",
        data={"question_id": question_id},
        files={"audio": ("answer.webm", b"\x1a\x45\xdf\xa3mock", "audio/webm")},
    )
    assert response.status_code == 409
    assert "already being processed" in response.json()["detail"]


def test_transcript_is_saved_when_evaluation_temporarily_fails(voice_client, monkeypatch):
    http, test_session, _ = voice_client
    started = start_voice(http, monkeypatch)
    monkeypatch.setattr(
        "app.routes.voice_interview.speech_to_text",
        lambda audio: {"transcript": "I would monitor the service.", "duration_seconds": 3.0},
    )
    monkeypatch.setattr(
        "app.routes.voice_interview.ai_service.evaluate_answer",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("provider unavailable")),
    )

    response = http.post(
        f"/voice/stt/{started.json()['session_id']}",
        files={"audio": ("answer.webm", b"\x1a\x45\xdf\xa3mock", "audio/webm")},
    )
    assert response.status_code == 503
    assert "transcript was saved" in response.json()["detail"]
    with test_session() as db:
        session = db.query(VoiceInterviewSession).one()
        assert session.transcript[-1]["text"] == "I would monitor the service."
        assert session.transcript[-1]["evaluation"] is None


def test_rate_limited_evaluation_can_be_retried_without_reuploading_audio(voice_client, monkeypatch):
    http, test_session, _ = voice_client
    started = start_voice(http, monkeypatch)
    session_id = started.json()["session_id"]
    monkeypatch.setattr(
        "app.routes.voice_interview.speech_to_text",
        lambda audio: {"transcript": "I would monitor the service.", "duration_seconds": 3.0},
    )
    monkeypatch.setattr(
        "app.routes.voice_interview.ai_service.evaluate_answer",
        lambda **kwargs: (_ for _ in ()).throw(HTTPException(status_code=429, detail="Rate limited")),
    )
    audio_response = http.post(
        f"/voice/stt/{session_id}",
        files={"audio": ("answer.webm", b"\x1a\x45\xdf\xa3mock", "audio/webm")},
    )
    assert audio_response.status_code == 429
    assert "transcript was saved" in audio_response.json()["detail"]

    monkeypatch.setattr(
        "app.routes.voice_interview.ai_service.evaluate_answer",
        lambda **kwargs: {"score": 7, "feedback": "Good response."},
    )
    retry = http.post(f"/voice/evaluate/{session_id}")
    assert retry.status_code == 200
    assert retry.json()["transcript"] == "I would monitor the service."
    assert retry.json()["evaluation"]["score"] == 7
    with test_session() as db:
        saved = db.query(VoiceInterviewSession).one()
        assert sum(turn["role"] == "candidate" for turn in saved.transcript) == 1


def test_audio_upload_limit_is_rejected(voice_client, monkeypatch):
    http, _, _ = voice_client
    started = start_voice(http, monkeypatch)
    oversized = b"\x1a\x45\xdf\xa3" + (b"x" * (8 * 1024 * 1024))
    response = http.post(
        f"/voice/stt/{started.json()['session_id']}",
        files={"audio": ("answer.webm", oversized, "audio/webm")},
    )
    assert response.status_code == 413
    assert "8 MB" in response.json()["detail"]


def test_audio_signature_formats_and_no_speech_errors():
    from app.services.voice_interview_service import (
        MAX_AUDIO_BYTES,
        _guess_audio_extension,
        speech_to_text,
    )

    assert _guess_audio_extension(b"RIFFxxxx") == ".wav"
    assert _guess_audio_extension(b"OggSxxxx") == ".ogg"
    assert _guess_audio_extension(b"ID3xxxx") == ".mp3"
    assert _guess_audio_extension(b"\x1a\x45\xdf\xa3xxxx") == ".webm"
    with pytest.raises(ValueError, match="exceeds"):
        speech_to_text(b"\x1a\x45\xdf\xa3" + (b"x" * MAX_AUDIO_BYTES))
