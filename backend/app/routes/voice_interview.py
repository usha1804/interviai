"""Voice Interview routes"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import asyncio
import os

from app.database import get_db
from app.models.models import User, VoiceInterviewSession
from app.utils.auth import get_current_user
from app.services.voice_interview_service import (
    text_to_speech, speech_to_text, analyze_speech, build_transcript_entry
)
from app.config import settings
import logging, traceback
from app.services.ai_service import ai_service

router = APIRouter(prefix="/voice", tags=["voice"])


class StartVoiceRequest(BaseModel):
    interview_type: str = "TECHNICAL"
    category: str = "Technical"


class TTSRequest(BaseModel):
    text: str
    session_id: int
    index: int = 0


@router.post("/start")
async def start_session(
    body: StartVoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = VoiceInterviewSession(
        user_id=current_user.id,
        interview_type=body.interview_type,
        transcript=[],
        status="IN_PROGRESS",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Generate first question
    first_q = ai_service.generate_interview_question(
        category=body.category, difficulty="MEDIUM", question_type="TECHNICAL"
    )

    transcript = [build_transcript_entry("ai", first_q)]
    session.transcript = transcript
    db.commit()

    return {"session_id": session.id, "first_question": first_q}


@router.post("/tts")
async def tts(
    body: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    """Convert text to speech, return audio file."""
    try:
        # Run TTS with a longer timeout for longer audio generation tasks.
        path, media_type = await asyncio.wait_for(
            text_to_speech(body.text, body.session_id, body.index), timeout=45
        )
        filename = os.path.basename(path)
        return FileResponse(path, media_type=media_type, filename=filename)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="TTS timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.post("/stt/{session_id}")
async def stt(
    session_id: int,
    audio: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Transcribe audio, evaluate answer, generate next question."""
    session = db.query(VoiceInterviewSession).filter(
        VoiceInterviewSession.id == session_id,
        VoiceInterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if audio is None:
        raise HTTPException(status_code=400, detail="Audio file is required.")

    audio_bytes = await audio.read()

    try:
        # Run the CPU-bound transcription in a thread and allow more time for longer files.
        stt_result = await asyncio.wait_for(
            asyncio.to_thread(speech_to_text, audio_bytes), timeout=45
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="STT timed out")
    except Exception as e:
        logging.error("STT failed:\n%s", traceback.format_exc())
        detail = f"STT failed: {str(e)}"
        if settings.DEBUG:
            detail = f"{detail}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=detail)

    transcript_text = stt_result["transcript"]
    speech_analysis = analyze_speech(transcript_text, stt_result["duration_seconds"])

    transcript = list(session.transcript or [])
    transcript.append(build_transcript_entry("candidate", transcript_text))

    # Get last AI question
    ai_questions = [t for t in transcript if t["role"] == "ai"]
    last_question = ai_questions[-1]["text"] if ai_questions else "Tell me about yourself."

    # Evaluate answer
    evaluation = ai_service.evaluate_answer(
        question=last_question,
        user_answer=transcript_text,
        category="Technical",
        difficulty="MEDIUM",
    )

    # Generate next question
    next_q = ai_service.generate_interview_question(
        category="Technical", difficulty="MEDIUM", question_type="TECHNICAL"
    )
    transcript.append(build_transcript_entry("ai", next_q))

    session.transcript = transcript
    session.filler_word_count = (session.filler_word_count or 0) + speech_analysis["filler_word_count"]
    session.speaking_speed = speech_analysis["speaking_speed"]
    db.commit()

    return {
        "transcript": transcript_text,
        "speech_analysis": speech_analysis,
        "evaluation": evaluation,
        "next_question": next_q,
    }


@router.post("/end/{session_id}")
async def end_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(VoiceInterviewSession).filter(
        VoiceInterviewSession.id == session_id,
        VoiceInterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    transcript = session.transcript or []
    candidate_turns = [t for t in transcript if t["role"] == "candidate"]
    all_text = " ".join(t["text"] for t in candidate_turns)

    # Final speech analysis
    word_count = len(all_text.split())
    comm_score = max(0, 100 - min((session.filler_word_count or 0) * 3, 30))

    session.overall_score = comm_score
    session.communication_score = comm_score
    session.status = "COMPLETED"
    session.completed_at = datetime.utcnow()
    db.commit()

    return {
        "session_id": session_id,
        "total_turns": len(candidate_turns),
        "filler_word_count": session.filler_word_count,
        "speaking_speed": session.speaking_speed,
        "communication_score": comm_score,
        "transcript": transcript,
    }
