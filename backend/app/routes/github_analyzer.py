"""GitHub Analyzer routes"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, GitHubAnalysis
from app.utils.auth import get_current_user
from app.services.github_service import analyze_github

router = APIRouter(prefix="/github", tags=["github"])


class GitHubRequest(BaseModel):
    github_url: str


@router.post("/analyze")
async def analyze(
    body: GitHubRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = analyze_github(body.github_url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    record = GitHubAnalysis(
        user_id=current_user.id,
        github_url=body.github_url,
        username=result.get("username"),
        github_score=result.get("github_score"),
        project_quality_score=result.get("project_quality_score"),
        coding_activity_score=result.get("coding_activity_score"),
        open_source_score=result.get("open_source_score"),
        languages=result.get("languages"),
        frameworks=result.get("frameworks"),
        top_repos=result.get("top_repos"),
        total_stars=result.get("total_stars", 0),
        total_forks=result.get("total_forks", 0),
        commit_frequency=result.get("commit_frequency"),
        recommendations=result.get("recommendations"),
        ai_summary=result.get("ai_summary"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {**result, "analysis_id": record.id}


@router.get("/latest")
async def get_latest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(GitHubAnalysis).filter(
        GitHubAnalysis.user_id == current_user.id
    ).order_by(GitHubAnalysis.analyzed_at.desc()).first()
    if not record:
        return {"analysis": None}
    return {
        "analysis": {
            "id": record.id, "github_url": record.github_url,
            "username": record.username, "github_score": record.github_score,
            "project_quality_score": record.project_quality_score,
            "coding_activity_score": record.coding_activity_score,
            "open_source_score": record.open_source_score,
            "languages": record.languages, "frameworks": record.frameworks,
            "top_repos": record.top_repos, "total_stars": record.total_stars,
            "commit_frequency": record.commit_frequency,
            "recommendations": record.recommendations,
            "ai_summary": record.ai_summary,
            "analyzed_at": record.analyzed_at.isoformat(),
        }
    }
