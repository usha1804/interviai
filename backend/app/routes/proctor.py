"""Centralized proctoring routes"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, ProctoringSession
from app.utils.auth import get_current_user
from app.services.proctoring_service import (
    compute_proctoring_score, compute_confidence_score,
    generate_proctoring_feedback, generate_readiness_report,
)

router = APIRouter(prefix="/proctor", tags=["proctoring"])


# ── Pydantic models ────────────────────────────────────────────────

class StartSession(BaseModel):
    session_key: str        # e.g. "interview_3499" or "coding_12"
    session_type: str       # TECHNICAL | HR | CODING | RESUME


class ViolationEvent(BaseModel):
    session_key: str
    event_type: str         # TAB_SWITCH | COPY_PASTE | NO_FACE | MULTI_FACE | FULLSCREEN_EXIT | LOOK_AWAY
    detail: Optional[str] = None


class EndSession(BaseModel):
    session_key: str
    # Aggregated behavioural metrics from frontend
    eye_contact_pct: float = 70
    attention_pct: float = 70
    movement_score: float = 30
    smile_pct: float = 40


class ReadinessRequest(BaseModel):
    technical_score: float = 0
    coding_score: float = 0
    communication_score: float = 0
    confidence_score: float = 0
    proctoring_score: float = 0


class ProctoringReport(BaseModel):
    session_key: str
    session_type: str
    proctoring_score: float
    confidence_score: float
    eye_contact_score: float
    posture_score: float
    expression_score: float
    tab_switches: int
    copy_paste_count: int
    face_not_detected: int
    multiple_faces: int
    fullscreen_exits: int
    looking_away: int
    ai_feedback: Optional[dict]
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/start", status_code=201)
async def start_proctoring(
    body: StartSession,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create (or reset) a proctoring session."""
    # Idempotent — reset if already exists
    existing = db.query(ProctoringSession).filter(
        ProctoringSession.session_key == body.session_key,
        ProctoringSession.user_id == current_user.id,
    ).first()

    if existing:
        existing.tab_switches = 0
        existing.copy_paste_count = 0
        existing.face_not_detected = 0
        existing.multiple_faces = 0
        existing.fullscreen_exits = 0
        existing.looking_away = 0
        existing.events = []
        existing.started_at = datetime.utcnow()
        existing.ended_at = None
        db.commit()
        return {"status": "reset", "session_key": body.session_key}

    record = ProctoringSession(
        user_id=current_user.id,
        session_key=body.session_key,
        session_type=body.session_type,
        events=[],
    )
    db.add(record)
    db.commit()
    return {"status": "started", "session_key": body.session_key}


@router.post("/event")
async def log_event(
    body: ViolationEvent,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log a single violation or behavioural event. Auto-creates session if missing."""
    record = db.query(ProctoringSession).filter(
        ProctoringSession.session_key == body.session_key,
        ProctoringSession.user_id == current_user.id,
    ).first()
    if not record:
        # Auto-create session so events are never lost
        record = ProctoringSession(
            user_id=current_user.id,
            session_key=body.session_key,
            session_type="TECHNICAL",
            events=[],
        )
        db.add(record)
        db.flush()

    # Increment counter
    counters = {
        "TAB_SWITCH": "tab_switches",
        "COPY_PASTE": "copy_paste_count",
        "NO_FACE": "face_not_detected",
        "MULTI_FACE": "multiple_faces",
        "FULLSCREEN_EXIT": "fullscreen_exits",
        "LOOK_AWAY": "looking_away",
    }
    field = counters.get(body.event_type)
    if field:
        current_val = getattr(record, field, 0) or 0
        setattr(record, field, current_val + 1)

    # Append to event log
    events = list(record.events or [])
    events.append({
        "ts": datetime.utcnow().isoformat(),
        "type": body.event_type,
        "detail": body.detail,
    })
    record.events = events

    db.commit()
    return {"logged": body.event_type}


@router.post("/end", response_model=ProctoringReport)
async def end_proctoring(
    body: EndSession,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Finalize session — compute all scores and generate AI feedback."""
    record = db.query(ProctoringSession).filter(
        ProctoringSession.session_key == body.session_key,
        ProctoringSession.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Proctoring session not found.")

    violations = {
        "tab_switches": record.tab_switches or 0,
        "copy_paste_count": record.copy_paste_count or 0,
        "face_not_detected": record.face_not_detected or 0,
        "multiple_faces": record.multiple_faces or 0,
        "fullscreen_exits": record.fullscreen_exits or 0,
        "looking_away": record.looking_away or 0,
    }
    behaviour = compute_confidence_score({
        "eye_contact_pct": body.eye_contact_pct,
        "attention_pct": body.attention_pct,
        "movement_score": body.movement_score,
        "smile_pct": body.smile_pct,
    })

    proctoring_score = compute_proctoring_score(violations)
    feedback = generate_proctoring_feedback(
        scores={**behaviour, "proctoring_score": proctoring_score},
        violations=violations,
        session_type=record.session_type,
    )

    record.proctoring_score = proctoring_score
    record.eye_contact_score = behaviour["eye_contact_score"]
    record.posture_score = behaviour["posture_score"]
    record.expression_score = behaviour["expression_score"]
    record.confidence_score = behaviour["confidence_score"]
    record.ai_feedback = feedback
    record.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(record)

    return ProctoringReport(
        session_key=record.session_key,
        session_type=record.session_type,
        proctoring_score=record.proctoring_score,
        confidence_score=record.confidence_score,
        eye_contact_score=record.eye_contact_score,
        posture_score=record.posture_score,
        expression_score=record.expression_score,
        tab_switches=record.tab_switches,
        copy_paste_count=record.copy_paste_count,
        face_not_detected=record.face_not_detected,
        multiple_faces=record.multiple_faces,
        fullscreen_exits=record.fullscreen_exits,
        looking_away=record.looking_away,
        ai_feedback=record.ai_feedback,
        started_at=record.started_at,
        ended_at=record.ended_at,
    )


@router.get("/report/{session_key}", response_model=ProctoringReport)
async def get_report(
    session_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(ProctoringSession).filter(
        ProctoringSession.session_key == session_key,
        ProctoringSession.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Report not found.")
    return ProctoringReport(
        session_key=record.session_key,
        session_type=record.session_type,
        proctoring_score=record.proctoring_score or 0,
        confidence_score=record.confidence_score or 0,
        eye_contact_score=record.eye_contact_score or 0,
        posture_score=record.posture_score or 0,
        expression_score=record.expression_score or 0,
        tab_switches=record.tab_switches or 0,
        copy_paste_count=record.copy_paste_count or 0,
        face_not_detected=record.face_not_detected or 0,
        multiple_faces=record.multiple_faces or 0,
        fullscreen_exits=record.fullscreen_exits or 0,
        looking_away=record.looking_away or 0,
        ai_feedback=record.ai_feedback,
        started_at=record.started_at,
        ended_at=record.ended_at,
    )


@router.post("/readiness-report")
async def readiness_report(
    body: ReadinessRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate final Interview Readiness Report combining all scores."""
    report = generate_readiness_report(body.dict())
    return report
