"""Voice interview API routes."""
import asyncio
import copy
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, VoiceInterviewSession
from app.services.ai_service import ai_service
from app.services.voice_interview_service import (
    analyze_speech,
    build_transcript_entry,
    speech_to_text,
    text_to_speech,
)
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])
MAX_QUESTIONS = 5
MAX_AUDIO_BYTES = 8 * 1024 * 1024


class StartVoiceRequest(BaseModel):
    interview_type: str = "TECHNICAL"
    category: str = "Technical"

    @field_validator("interview_type")
    @classmethod
    def validate_interview_type(cls, value):
        value = value.strip().upper()
        if value not in {"TECHNICAL", "HR"}:
            raise ValueError("Interview type must be TECHNICAL or HR.")
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value):
        value = value.strip()
        if value not in {"Technical", "Java", "Python", "React", "SQL", "Behavioral", "Leadership"}:
            raise ValueError("Select a supported interview category.")
        return value


class TTSRequest(BaseModel):
    text: str
    session_id: int
    index: int = 0


def _session_for_user(db: Session, session_id: int, user_id: int) -> VoiceInterviewSession:
    session = db.query(VoiceInterviewSession).filter(
        VoiceInterviewSession.id == session_id,
        VoiceInterviewSession.user_id == user_id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Voice interview session not found.")
    return session


def _delete_tts_file(path: str):
    try:
        if path:
            os.unlink(path)
    except FileNotFoundError:
        pass


def _category(transcript: list) -> str:
    return next(
        (turn.get("category") for turn in transcript if turn.get("role") == "ai" and turn.get("category")),
        "Technical",
    )


def _question_type(session: VoiceInterviewSession) -> str:
    return "HR" if session.interview_type == "HR" else "TECHNICAL"


def _make_question(session: VoiceInterviewSession, transcript: list) -> str:
    previous_questions = [turn["text"] for turn in transcript if turn.get("role") == "ai"]
    return ai_service.generate_interview_question(
        category=_category(transcript),
        difficulty="MEDIUM",
        question_type=_question_type(session),
        previous_topics=previous_questions,
    )


def _answer_count(transcript: list) -> int:
    return sum(turn.get("role") == "candidate" for turn in transcript)


def _ensure_question_ids(transcript: list) -> bool:
    """Backfill IDs for existing transcript records without changing their answers."""
    changed = False
    questions_by_number = {}
    question_number = 0
    answer_number = 0
    for turn in transcript:
        if turn.get("role") == "ai":
            question_number += 1
            if not turn.get("question_number"):
                turn["question_number"] = question_number
                changed = True
        elif turn.get("role") == "candidate":
            answer_number += 1
            if not turn.get("question_number"):
                turn["question_number"] = answer_number
                changed = True
    for turn in transcript:
        if turn.get("role") != "ai":
            continue
        if not turn.get("question_id"):
            turn["question_id"] = str(uuid.uuid4())
            changed = True
        if not turn.get("submission_status"):
            status = "answered" if any(
                answer.get("role") == "candidate"
                and answer.get("question_number") == turn.get("question_number")
                for answer in transcript
            ) else "pending"
            turn["submission_status"] = status
            changed = True
        questions_by_number[turn.get("question_number")] = turn["question_id"]
    for turn in transcript:
        if turn.get("role") == "candidate" and not turn.get("question_id"):
            turn["question_id"] = questions_by_number.get(turn.get("question_number"))
            if turn["question_id"]:
                changed = True
    return changed


def _question_for_id(transcript: list, question_id: str):
    return next(
        (turn for turn in transcript if turn.get("role") == "ai" and turn.get("question_id") == question_id),
        None,
    )


def _answer_for_question(transcript: list, question_id: str):
    return next(
        (
            turn for turn in transcript
            if turn.get("role") == "candidate" and turn.get("question_id") == question_id
        ),
        None,
    )


def _question_response(question: dict, completed: bool = False) -> dict:
    return {
        "next_question": None if completed else question["text"],
        "current_question_id": None if completed else question["question_id"],
        "current_question_status": None if completed else question.get("submission_status", "pending"),
        "completed": completed,
        "question_number": MAX_QUESTIONS if completed else question.get("question_number"),
        "total_questions": MAX_QUESTIONS,
    }


def _next_question_response(session: VoiceInterviewSession, transcript: list) -> dict:
    if _answer_count(transcript) >= MAX_QUESTIONS:
        return {
            "next_question": None,
            "current_question_id": None,
            "current_question_status": None,
            "completed": True,
            "question_number": MAX_QUESTIONS,
            "total_questions": MAX_QUESTIONS,
        }
    if transcript and transcript[-1].get("role") == "ai":
        return _question_response(transcript[-1])

    question = _make_question(session, transcript)
    number = _answer_count(transcript) + 1
    question_entry = {
        **build_transcript_entry("ai", question),
        "category": _category(transcript),
        "question_number": number,
        "question_id": str(uuid.uuid4()),
        "submission_status": "pending",
    }
    transcript.append(question_entry)
    session.transcript = transcript
    return _question_response(question_entry)


def _answer_response(session: VoiceInterviewSession, transcript: list, answer: dict, evaluation=None, already_processed=False):
    next_result = _next_question_response(session, transcript)
    session.transcript = transcript
    return {
        "transcript": answer["text"],
        "speech_analysis": answer.get("speech_analysis"),
        "evaluation": evaluation if evaluation is not None else answer.get("evaluation"),
        "answered_question_id": answer["question_id"],
        "already_processed": already_processed,
        **next_result,
    }


def _reset_question_submission(session: VoiceInterviewSession, question_id: str, db: Session):
    transcript = copy.deepcopy(session.transcript or [])
    question = _question_for_id(transcript, question_id)
    if question and not _answer_for_question(transcript, question_id):
        question["submission_status"] = "pending"
        question.pop("submission_started_at", None)
        session.transcript = transcript
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Could not release voice question %s after failed transcription", question_id)


def _reset_evaluation(session: VoiceInterviewSession, question_id: Optional[str], db: Session):
    transcript = copy.deepcopy(session.transcript or [])
    candidate = _answer_for_question(transcript, question_id) if question_id else None
    if candidate and candidate.get("evaluation") is None:
        candidate["evaluation_status"] = "pending"
        candidate.pop("evaluation_started_at", None)
        session.transcript = transcript
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Could not release voice answer evaluation for session %s", session.id)


async def _evaluate_pending(session: VoiceInterviewSession, db: Session, question_id: Optional[str] = None):
    session = db.query(VoiceInterviewSession).filter(
        VoiceInterviewSession.id == session.id,
        VoiceInterviewSession.user_id == session.user_id,
    ).with_for_update().populate_existing().first()
    transcript = copy.deepcopy(session.transcript or [])
    _ensure_question_ids(transcript)
    candidate = next(
        (
            turn for turn in reversed(transcript)
            if turn.get("role") == "candidate"
            and (question_id is None or turn.get("question_id") == question_id)
        ),
        None,
    )
    if not candidate:
        raise HTTPException(status_code=409, detail="There is no saved answer to evaluate.")
    if candidate.get("evaluation") is not None:
        return candidate["evaluation"]
    if candidate.get("evaluation_status") == "processing":
        started = candidate.get("evaluation_started_at")
        try:
            is_stale = started and (datetime.utcnow() - datetime.fromisoformat(started)).total_seconds() > 180
        except (TypeError, ValueError):
            is_stale = True
        if not is_stale:
            raise HTTPException(status_code=409, detail="This answer's evaluation is already in progress.")

    candidate["evaluation_status"] = "processing"
    candidate["evaluation_started_at"] = datetime.utcnow().isoformat()
    session.transcript = transcript
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Could not reserve answer evaluation for session %s", session.id)
        raise HTTPException(status_code=500, detail="Could not begin evaluating the saved answer.") from exc

    try:
        evaluation = await asyncio.to_thread(
            ai_service.evaluate_answer,
            question=candidate["question"],
            user_answer=candidate["text"],
            category=_category(transcript),
            difficulty="MEDIUM",
        )
    except HTTPException as exc:
        _reset_evaluation(session, candidate["question_id"], db)
        logger.warning("Voice evaluation failed for session %s with HTTP %s", session.id, exc.status_code)
        if exc.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Your transcript was saved, but AI evaluation is rate limited. Retry evaluation shortly.",
            ) from exc
        raise HTTPException(
            status_code=503,
            detail="Your transcript was saved, but AI evaluation is temporarily unavailable. Retry evaluation.",
        ) from exc
    except Exception as exc:
        _reset_evaluation(session, candidate["question_id"], db)
        logger.exception("Voice answer evaluation failed for session %s", session.id)
        raise HTTPException(
            status_code=503,
            detail="Your transcript was saved, but AI evaluation is temporarily unavailable. Retry evaluation.",
        ) from exc
    transcript = copy.deepcopy(session.transcript or [])
    candidate = _answer_for_question(transcript, candidate["question_id"])
    candidate["evaluation"] = evaluation
    candidate["evaluation_status"] = "complete"
    candidate.pop("evaluation_started_at", None)
    session.transcript = transcript
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Could not persist answer evaluation for session %s", session.id)
        raise HTTPException(
            status_code=500,
            detail="Answer was transcribed and saved, but its evaluation could not be saved. Retry evaluation.",
        ) from exc
    return evaluation


@router.post("/start")
async def start_session(
    body: StartVoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question_type = body.interview_type
    try:
        first_question = await asyncio.to_thread(
            ai_service.generate_interview_question,
            category=body.category,
            difficulty="MEDIUM",
            question_type=question_type,
        )
    except Exception as exc:
        logger.exception("Could not generate the first voice interview question")
        raise HTTPException(status_code=503, detail="Could not generate the first question. Please retry.") from exc

    session = VoiceInterviewSession(
        user_id=current_user.id,
        interview_type=body.interview_type,
        transcript=[{
            **build_transcript_entry("ai", first_question),
            "category": body.category,
            "question_number": 1,
            "question_id": str(uuid.uuid4()),
            "submission_status": "pending",
        }],
        status="IN_PROGRESS",
    )
    try:
        db.add(session)
        db.commit()
        db.refresh(session)
    except Exception:
        db.rollback()
        logger.exception("Could not save voice interview session")
        raise HTTPException(status_code=500, detail="Could not save the voice interview session.")
    return {
        "session_id": session.id,
        "first_question": first_question,
        "question_number": 1,
        "current_question_id": session.transcript[0]["question_id"],
        "total_questions": MAX_QUESTIONS,
        "status": session.status,
    }


@router.get("/session/{session_id}")
async def get_voice_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _session_for_user(db, session_id, current_user.id)
    transcript = copy.deepcopy(session.transcript or [])
    if _ensure_question_ids(transcript):
        session.transcript = transcript
        db.commit()
    current_question = transcript[-1] if transcript and transcript[-1].get("role") == "ai" else None
    latest_answer = next(
        (turn for turn in reversed(transcript) if turn.get("role") == "candidate"),
        None,
    )
    return {
        "session_id": session.id,
        "status": session.status,
        "interview_type": session.interview_type,
        "transcript": transcript,
        "current_question": current_question.get("text") if current_question else None,
        "current_question_id": current_question.get("question_id") if current_question else None,
        "current_question_status": current_question.get("submission_status") if current_question else None,
        "question_number": current_question.get("question_number") if current_question else _answer_count(transcript),
        "total_questions": MAX_QUESTIONS,
        "evaluation_pending": bool(latest_answer and latest_answer.get("evaluation") is None),
        "completed": session.status == "COMPLETED",
        "summary": {
            "session_id": session.id,
            "total_turns": _answer_count(transcript),
            "filler_word_count": session.filler_word_count,
            "speaking_speed": session.speaking_speed,
            "communication_score": session.communication_score,
            "transcript": transcript,
            "status": session.status,
        } if session.status == "COMPLETED" else None,
    }


@router.post("/tts")
async def tts(
    body: TTSRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    try:
        path, media_type = await asyncio.wait_for(
            text_to_speech(body.text, body.session_id, body.index), timeout=45
        )
        background_tasks.add_task(_delete_tts_file, path)
        return FileResponse(path, media_type=media_type, filename=os.path.basename(path))
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Text-to-speech timed out.") from exc
    except Exception as exc:
        logger.exception("Voice TTS failed")
        raise HTTPException(status_code=503, detail="Could not generate spoken audio for the question.") from exc


@router.post("/stt/{session_id}")
async def stt(
    session_id: int,
    audio: Optional[UploadFile] = File(None),
    question_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(VoiceInterviewSession).filter(
        VoiceInterviewSession.id == session_id,
        VoiceInterviewSession.user_id == current_user.id,
    ).with_for_update().populate_existing().first()
    if not session:
        raise HTTPException(status_code=404, detail="Voice interview session not found.")
    if session.status != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="This voice interview is already completed.")
    if audio is None:
        raise HTTPException(status_code=400, detail="Audio file is required. Record an answer before submitting.")
    audio_bytes = await audio.read(MAX_AUDIO_BYTES + 1)
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="The audio recording is empty.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="The audio recording exceeds the 8 MB upload limit.")
    if audio.content_type and not (
        audio.content_type.startswith("audio/")
        or audio.content_type == "application/octet-stream"
    ):
        raise HTTPException(status_code=415, detail="Unsupported upload type. Submit an audio recording.")

    transcript = copy.deepcopy(session.transcript or [])
    _ensure_question_ids(transcript)
    if not question_id:
        if not transcript or transcript[-1].get("role") != "ai":
            raise HTTPException(
                status_code=409,
                detail="This answer has already been processed. Refresh the session to load its current question.",
            )
        question_id = transcript[-1]["question_id"]
    question = _question_for_id(transcript, question_id)
    if question is None:
        raise HTTPException(status_code=409, detail="The submitted question is not part of this interview session.")

    existing_answer = _answer_for_question(transcript, question_id)
    if existing_answer:
        evaluation = await _evaluate_pending(session, db, question_id)
        transcript = copy.deepcopy(session.transcript or [])
        existing_answer = _answer_for_question(transcript, question_id)
        try:
            response = _answer_response(
                session,
                transcript,
                existing_answer,
                evaluation=evaluation,
                already_processed=True,
            )
            session.transcript = transcript
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.exception("Could not resume voice progression for session %s", session_id)
            raise HTTPException(status_code=503, detail="Answer was saved. Retry to load the next question.") from exc
        return response

    if transcript[-1].get("role") != "ai" or transcript[-1].get("question_id") != question_id:
        raise HTTPException(status_code=409, detail="This is not the current unanswered question.")
    if question.get("submission_status") == "processing":
        started = question.get("submission_started_at")
        try:
            is_stale = started and (datetime.utcnow() - datetime.fromisoformat(started)).total_seconds() > 180
        except (TypeError, ValueError):
            is_stale = True
        if not is_stale:
            raise HTTPException(status_code=409, detail="This question's audio is already being processed.")

    question["submission_status"] = "processing"
    question["submission_started_at"] = datetime.utcnow().isoformat()
    session.transcript = transcript
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Could not reserve voice question %s for submission", question_id)
        raise HTTPException(status_code=500, detail="Could not begin processing this answer. Please retry.") from exc

    try:
        stt_result = await asyncio.wait_for(asyncio.to_thread(speech_to_text, audio_bytes), timeout=60)
    except ValueError as exc:
        _reset_question_submission(session, question_id, db)
        message = str(exc)
        if "No speech" in message:
            raise HTTPException(status_code=422, detail=message) from exc
        if "empty" in message.casefold():
            raise HTTPException(status_code=400, detail=message) from exc
        if "8 MB" in message:
            raise HTTPException(status_code=413, detail=message) from exc
        raise HTTPException(status_code=415, detail=message) from exc
    except asyncio.TimeoutError as exc:
        _reset_question_submission(session, question_id, db)
        raise HTTPException(status_code=504, detail="Speech transcription timed out. Please retry.") from exc
    except Exception as exc:
        _reset_question_submission(session, question_id, db)
        logger.exception("Voice transcription failed for session %s", session_id)
        raise HTTPException(status_code=502, detail="Speech transcription failed. Please try recording again.") from exc

    transcript_text = (stt_result.get("transcript") or "").strip()
    if not transcript_text:
        _reset_question_submission(session, question_id, db)
        raise HTTPException(status_code=422, detail="No speech was recognized. Please record your answer again.")
    speech_analysis = analyze_speech(transcript_text, stt_result.get("duration_seconds", 0))
    current_question = transcript[-1]
    answer_entry = {
        **build_transcript_entry("candidate", transcript_text),
        "question": current_question["text"],
        "question_number": current_question.get("question_number", _answer_count(transcript) + 1),
        "question_id": question_id,
        "speech_analysis": speech_analysis,
        "evaluation": None,
    }
    current_question["submission_status"] = "answered"
    transcript.append(answer_entry)
    session.transcript = transcript
    session.filler_word_count = (session.filler_word_count or 0) + speech_analysis["filler_word_count"]
    session.speaking_speed = speech_analysis["speaking_speed"]
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Could not persist voice transcript for session %s", session_id)
        raise HTTPException(status_code=500, detail="Could not save the transcribed answer.") from exc

    evaluation = await _evaluate_pending(session, db, question_id)
    transcript = copy.deepcopy(session.transcript or [])
    try:
        answer = _answer_for_question(transcript, question_id)
        result = _answer_response(session, transcript, answer, evaluation=evaluation)
        session.transcript = transcript
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not generate next voice question for session %s", session_id)
        result = {
            "transcript": transcript_text,
            "speech_analysis": speech_analysis,
            "evaluation": evaluation,
            "answered_question_id": question_id,
            "already_processed": False,
            "next_question": None,
            "current_question_id": None,
            "current_question_status": None,
            "completed": False,
            "question_number": _answer_count(transcript) + 1,
            "total_questions": MAX_QUESTIONS,
            "next_question_error": "Answer saved and evaluated. Retry to load the next question.",
        }
    return result


@router.post("/evaluate/{session_id}")
async def retry_evaluation(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _session_for_user(db, session_id, current_user.id)
    evaluation = await _evaluate_pending(session, db)
    transcript = copy.deepcopy(session.transcript or [])
    candidate = next(turn for turn in reversed(transcript) if turn.get("role") == "candidate")
    try:
        next_result = _next_question_response(session, transcript)
        session.transcript = transcript
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not generate next voice question for session %s", session_id)
        next_result = {"next_question": None, "completed": False, "next_question_error": "Retry to load the next question."}
    return {
        "evaluation": evaluation,
        "transcript": candidate["text"],
        "speech_analysis": candidate.get("speech_analysis"),
        **next_result,
    }


@router.post("/next/{session_id}")
async def next_question(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _session_for_user(db, session_id, current_user.id)
    if session.status != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="This voice interview is already completed.")
    transcript = copy.deepcopy(session.transcript or [])
    if transcript and transcript[-1].get("role") == "candidate" and transcript[-1].get("evaluation") is None:
        raise HTTPException(status_code=409, detail="Retry answer evaluation before moving to the next question.")
    if _answer_count(transcript) < MAX_QUESTIONS and transcript and transcript[-1].get("role") == "candidate":
        try:
            result = _next_question_response(session, transcript)
            session.transcript = transcript
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.exception("Could not generate next voice question for session %s", session_id)
            raise HTTPException(status_code=503, detail="Could not generate the next question. Retry to try again.") from exc
        return result
    return _next_question_response(session, transcript)


@router.post("/end/{session_id}")
async def end_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _session_for_user(db, session_id, current_user.id)
    transcript = copy.deepcopy(session.transcript or [])
    candidate_turns = [turn for turn in transcript if turn.get("role") == "candidate"]
    if not candidate_turns:
        raise HTTPException(status_code=400, detail="Submit at least one recorded answer before finishing.")
    if any(turn.get("evaluation") is None for turn in candidate_turns):
        raise HTTPException(status_code=409, detail="Evaluate all saved answers before finishing the interview.")

    all_text = " ".join(turn["text"] for turn in candidate_turns)
    communication_score = max(0, 100 - min((session.filler_word_count or 0) * 3, 30))
    session.overall_score = communication_score
    session.communication_score = communication_score
    session.status = "COMPLETED"
    session.completed_at = datetime.utcnow()
    db.commit()
    return {
        "session_id": session_id,
        "total_turns": len(candidate_turns),
        "filler_word_count": session.filler_word_count,
        "speaking_speed": session.speaking_speed,
        "communication_score": communication_score,
        "transcript": transcript,
        "word_count": len(all_text.split()),
        "status": session.status,
    }
