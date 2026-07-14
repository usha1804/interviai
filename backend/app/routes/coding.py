"""Coding interview routes"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, CodingSession, CodingProblem, CodingSubmission
from app.utils.auth import get_current_user
from app.services.coding_service import (
    generate_coding_problem, run_code, run_test_cases, ai_review_code
)

router = APIRouter(prefix="/coding", tags=["coding"])

TOPICS = [
    "Arrays", "Strings", "HashMaps", "Trees", "Graphs",
    "Dynamic Programming", "Stacks", "Queues", "Linked Lists",
    "Binary Search", "Recursion",
]


# ── Request / Response models ──────────────────────────────────────

class ProblemRequest(BaseModel):
    topic: Optional[str] = "Arrays"
    difficulty: str = "MEDIUM"
    language: str = "python"


class RunCodeRequest(BaseModel):
    code: str
    language: str
    stdin: str = ""


class SubmitRequest(BaseModel):
    session_id: int
    problem_data: dict   # full problem dict (returned from /problem)
    code: str
    language: str


class ProblemResponse(BaseModel):
    session_id: int
    problem: dict


class RunResult(BaseModel):
    output: str
    stderr: str = ""
    compile_error: str = ""
    status: str = ""


class SubmitResult(BaseModel):
    score: float
    passed_tests: int
    total_tests: int
    time_complexity: str
    space_complexity: str
    ai_feedback: dict


class HistoryItem(BaseModel):
    id: int
    difficulty: str
    language: str
    score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/problem", response_model=ProblemResponse)
async def get_problem(
    req: ProblemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a coding problem and create a session."""
    problem = generate_coding_problem(req.topic, req.difficulty)

    # Store solution_code server-side only — never expose to frontend
    solution_code = problem.pop("solution_code", "")

    # Persist problem (store solution_code in DB for future reference)
    db_problem = CodingProblem(
        title=problem.get("title", "Problem"),
        description=problem.get("description", ""),
        difficulty=req.difficulty,
        topic=req.topic,
        constraints=problem.get("constraints", ""),
        sample_input=problem.get("sample_input", ""),
        sample_output=problem.get("sample_output", ""),
        test_cases=problem.get("test_cases", []),
        expected_complexity=problem.get("expected_complexity", ""),
    )
    db.add(db_problem)
    db.flush()

    # Create session — store solution_code and problem_id for submit validation
    session = CodingSession(
        user_id=current_user.id,
        difficulty=req.difficulty,
        language=req.language,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Attach solution_code and test_cases to session in memory via problem dict
    # (solution_code is stripped from response — only starter_code goes to frontend)
    problem["_solution_code"] = solution_code  # kept in problem_data sent back
    return ProblemResponse(session_id=session.id, problem=problem)


@router.post("/run", response_model=RunResult)
async def run(
    req: RunCodeRequest,
    current_user: User = Depends(get_current_user),
):
    """Run code against custom stdin — used for 'Run' button."""
    result = run_code(req.code, req.language, req.stdin)
    return RunResult(
        output=result.get("output") or "",
        stderr=result.get("stderr") or "",
        compile_error=result.get("compile_error") or "",
        status=result.get("status") or "",
    )


@router.post("/submit", response_model=SubmitResult)
async def submit(
    req: SubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit candidate's solution — run test cases against CANDIDATE code + AI review."""
    session = db.query(CodingSession).filter(
        CodingSession.id == req.session_id,
        CodingSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Coding session not found.")

    test_cases = req.problem_data.get("test_cases", [])
    # Run the CANDIDATE'S code against test cases (not solution_code)
    test_result = run_test_cases(req.code, req.language, test_cases)

    review = ai_review_code(
        problem=req.problem_data.get("description", ""),
        code=req.code,
        language=req.language,
        test_result=test_result,
    )

    score = float(review.get("score", 0))

    # Persist submission
    submission = CodingSubmission(
        session_id=req.session_id,
        code=req.code,
        language=req.language,
        score=score,
        passed_tests=test_result["passed"],
        total_tests=test_result["total"],
        time_complexity=review.get("time_complexity", ""),
        space_complexity=review.get("space_complexity", ""),
        ai_feedback=review,
    )
    db.add(submission)

    # Update session score
    session.score = score
    db.commit()

    return SubmitResult(
        score=score,
        passed_tests=test_result["passed"],
        total_tests=test_result["total"],
        time_complexity=review.get("time_complexity", "N/A"),
        space_complexity=review.get("space_complexity", "N/A"),
        ai_feedback=review,
    )


@router.get("/history", response_model=List[HistoryItem])
async def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(CodingSession)
        .filter(CodingSession.user_id == current_user.id)
        .order_by(CodingSession.created_at.desc())
        .limit(20)
        .all()
    )
    return sessions
