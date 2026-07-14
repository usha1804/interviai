"""Recruiter Dashboard routes — requires ADMIN or RECRUITER role"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, RecruiterNote
from app.utils.auth import get_current_user
from app.services.recruiter_service import (
    get_all_candidates, get_candidate_profile, generate_hiring_decision
)

router = APIRouter(prefix="/recruiter", tags=["recruiter"])


def _require_recruiter(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("ADMIN", "RECRUITER"):
        raise HTTPException(status_code=403, detail="Recruiter access required.")
    return current_user


class NoteRequest(BaseModel):
    candidate_id: int
    note: str
    rating: Optional[int] = None
    decision: Optional[str] = None


@router.get("/candidates")
async def list_candidates(
    search: str = "",
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(_require_recruiter),
    db: Session = Depends(get_db),
):
    candidates = get_all_candidates(db, search=search, skip=skip, limit=limit)
    return {"candidates": candidates, "total": len(candidates)}


@router.get("/candidate/{candidate_id}")
async def get_candidate(
    candidate_id: int,
    current_user: User = Depends(_require_recruiter),
    db: Session = Depends(get_db),
):
    profile = get_candidate_profile(candidate_id, db)
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return profile


@router.post("/hiring-decision/{candidate_id}")
async def hiring_decision(
    candidate_id: int,
    current_user: User = Depends(_require_recruiter),
    db: Session = Depends(get_db),
):
    decision = generate_hiring_decision(candidate_id, db)
    return decision


@router.post("/note")
async def save_note(
    body: NoteRequest,
    current_user: User = Depends(_require_recruiter),
    db: Session = Depends(get_db),
):
    note = RecruiterNote(
        recruiter_id=current_user.id,
        candidate_id=body.candidate_id,
        note=body.note,
        rating=body.rating,
        decision=body.decision,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "message": "Note saved."}


@router.get("/notes/{candidate_id}")
async def get_notes(
    candidate_id: int,
    current_user: User = Depends(_require_recruiter),
    db: Session = Depends(get_db),
):
    notes = db.query(RecruiterNote).filter(
        RecruiterNote.candidate_id == candidate_id,
        RecruiterNote.recruiter_id == current_user.id,
    ).order_by(RecruiterNote.created_at.desc()).all()
    return [
        {"id": n.id, "note": n.note, "rating": n.rating,
         "decision": n.decision, "created_at": n.created_at.isoformat()}
        for n in notes
    ]
