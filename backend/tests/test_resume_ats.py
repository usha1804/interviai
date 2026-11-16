import io
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from docx import Document
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.models import ATSReport, Resume, User
from app.routes import ats as ats_routes
from app.routes import resume as resume_routes
from app.services import ats_service
from app.utils.auth import get_current_user


@pytest.fixture
def resume_client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with factory() as db:
        db.add_all([
            User(name="Resume Tester", email="resume@example.com", password="hash"),
            User(name="Other Tester", email="other@example.com", password="hash"),
        ])
        db.commit()
        user = db.query(User).filter_by(email="resume@example.com").one()
        user_id = user.id

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(resume_routes.router)
    app.include_router(ats_routes.router)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=user_id,
        name="Resume Tester",
    )
    monkeypatch.setattr(resume_routes, "UPLOAD_DIR", str(tmp_path / "resumes"))
    monkeypatch.setattr(
        resume_routes,
        "parse_resume_with_ai",
        lambda text: {"skills": ["Python"], "technologies": [], "projects": [], "experience": [], "education": []},
    )

    with TestClient(app) as client:
        client.app.state.test_session_factory = factory
        client.app.state.test_user_id = user_id
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def make_pdf(text=None):
    output = io.BytesIO()
    pdf = canvas.Canvas(output)
    if text:
        pdf.drawString(72, 720, text)
    pdf.save()
    return output.getvalue()


def make_docx():
    doc = Document()
    doc.add_paragraph("Full-stack developer with Python experience")
    table = doc.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "Project: FastAPI resume analyzer"
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()


def test_pdf_upload_extracts_persists_and_returns_status(resume_client):
    response = resume_client.post(
        "/resume/upload",
        files={"file": ("resume.pdf", make_pdf("Python software engineer"), "application/pdf")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["extraction_status"] == "completed"
    assert "Python software engineer" in payload["resume_text"]
    assert payload["user_id"] == resume_client.app.state.test_user_id

    second_upload = resume_client.post(
        "/resume/upload",
        files={
            "file": (
                "second.docx",
                make_docx(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    latest = resume_client.get("/resume/latest")
    assert second_upload.status_code == 201
    assert latest.json()["id"] == second_upload.json()["id"]

    with resume_client.app.state.test_session_factory() as db:
        saved = db.query(Resume).filter_by(id=payload["id"]).one()
        assert saved.resume_text == payload["resume_text"]
        assert saved.user_id == resume_client.app.state.test_user_id


def test_docx_upload_extracts_paragraphs_and_table_content(resume_client):
    response = resume_client.post(
        "/resume/upload",
        files={
            "file": (
                "resume.docx",
                make_docx(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    assert "Full-stack developer" in response.json()["resume_text"]
    assert "FastAPI resume analyzer" in response.json()["resume_text"]


def test_invalid_and_empty_scanned_resumes_are_rejected_without_records(resume_client):
    invalid = resume_client.post(
        "/resume/upload",
        files={"file": ("resume.pdf", b"not a PDF", "application/pdf")},
    )
    empty = resume_client.post(
        "/resume/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    oversized = resume_client.post(
        "/resume/upload",
        files={
            "file": (
                "oversized.pdf",
                b"%PDF-" + (b"0" * resume_routes.MAX_FILE_SIZE),
                "application/pdf",
            )
        },
    )
    scanned = resume_client.post(
        "/resume/upload",
        files={"file": ("scanned.pdf", make_pdf(), "application/pdf")},
    )
    unsupported = resume_client.post(
        "/resume/upload",
        files={"file": ("resume.doc", b"legacy", "application/msword")},
    )

    assert invalid.status_code == 400
    assert empty.status_code == 400
    assert oversized.status_code == 400
    assert "5 MB" in oversized.json()["detail"]
    assert scanned.status_code == 422
    assert "scanned or image-only" in scanned.json()["detail"]
    assert unsupported.status_code == 400
    with resume_client.app.state.test_session_factory() as db:
        assert db.query(Resume).count() == 0


def test_analyzer_uses_latest_extracted_resume_for_authenticated_user(resume_client, monkeypatch, tmp_path):
    with resume_client.app.state.test_session_factory() as db:
        valid = Resume(
            user_id=resume_client.app.state.test_user_id,
            file_name="valid.pdf",
            file_path="valid.pdf",
            resume_text="Python engineer",
        )
        empty_legacy_record = Resume(
            user_id=resume_client.app.state.test_user_id,
            file_name="legacy.pdf",
            file_path="legacy.pdf",
            resume_text="",
            uploaded_at=datetime.utcnow() + timedelta(seconds=1),
        )
        db.add_all([valid, empty_legacy_record])
        db.commit()
        valid_resume_id = valid.id

    analyzed_text = []
    monkeypatch.setattr(
        ats_routes,
        "analyze_ats",
        lambda text, jd: analyzed_text.append((text, jd)) or {
            "ats_score": 70,
            "keyword_match_pct": 60,
            "matching_skills": ["Python"],
            "missing_skills": [],
            "missing_technologies": [],
            "strengths": [],
            "weaknesses": [],
            "improvements": [],
            "formatting_suggestions": [],
            "ai_summary": "Evidence-based match.",
        },
    )
    report_path = tmp_path / "ats-report.pdf"
    report_path.write_bytes(b"test pdf")
    monkeypatch.setattr(ats_routes, "generate_ats_pdf", lambda *args: str(report_path))

    response = resume_client.post(
        "/ats/analyze",
        json={"jd_text": "Python software engineering role"},
    )

    assert response.status_code == 200
    assert response.json()["has_pdf"] is True
    assert analyzed_text == [("Python engineer", "Python software engineering role")]
    downloaded = resume_client.get(f"/ats/report/{response.json()['report_id']}/pdf")
    assert downloaded.status_code == 200
    assert downloaded.content == b"test pdf"
    with resume_client.app.state.test_session_factory() as db:
        report = db.query(ATSReport).filter_by(id=response.json()["report_id"]).one()
        assert report.resume_id == valid_resume_id
        assert report.user_id == resume_client.app.state.test_user_id


def test_analyzer_rejects_empty_job_description_and_another_users_resume(resume_client):
    empty_jd = resume_client.post("/ats/analyze", json={"jd_text": "  "})
    missing_resume = resume_client.post(
        "/ats/analyze",
        json={"jd_text": "A valid job description"},
    )
    with resume_client.app.state.test_session_factory() as db:
        other_user = db.query(User).filter_by(email="other@example.com").one()
        foreign_resume = Resume(
            user_id=other_user.id,
            file_name="private.pdf",
            file_path="private.pdf",
            resume_text="Private resume content",
        )
        db.add(foreign_resume)
        db.commit()
        foreign_resume_id = foreign_resume.id

    foreign_resume_response = resume_client.post(
        "/ats/analyze",
        json={"resume_id": foreign_resume_id, "jd_text": "A valid job description"},
    )

    assert empty_jd.status_code == 422
    assert missing_resume.status_code == 422
    assert foreign_resume_response.status_code == 404


def test_ats_score_uses_matched_keywords_skills_and_ai_evaluations(monkeypatch):
    ai_result = {
        "job_keywords": ["Python", "FastAPI", "REST API"],
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["REST API"],
        "technical_skills": ["Python", "FastAPI"],
        "experience_match_pct": 80,
        "education_match_pct": 60,
        "project_match_pct": 100,
        "strengths": ["Python experience is present."],
        "weaknesses": ["REST API is not demonstrated."],
        "improvements": ["Add a relevant API project if applicable."],
        "formatting_suggestions": [],
        "ai_summary": "The resume demonstrates two of three requested skills.",
    }
    monkeypatch.setattr(ats_service, "get_groq_client", lambda: object())
    monkeypatch.setattr(
        ats_service,
        "_chat",
        lambda *args, **kwargs: json.dumps(ai_result),
    )

    result = ats_service.analyze_ats(
        "Python developer with FastAPI experience",
        "We need Python, FastAPI, and REST API experience.",
    )

    assert result["matching_skills"] == ["Python", "FastAPI"]
    assert result["missing_skills"] == ["REST API"]
    assert result["missing_required_skills"] == []
    assert result["keyword_match_pct"] == pytest.approx(66.7)
    assert result["skills_match_pct"] == pytest.approx(66.7)
    assert result["ats_score"] == 70
    assert result["recommended_keywords"] == ["REST API"]


def test_ats_invalid_ai_result_fails_instead_of_returning_a_placeholder_score(monkeypatch):
    monkeypatch.setattr(ats_service, "get_groq_client", lambda: object())
    monkeypatch.setattr(ats_service, "_chat", lambda *args, **kwargs: "not JSON")

    with pytest.raises(HTTPException) as error:
        ats_service.analyze_ats("Python developer", "Python engineering role")

    assert error.value.status_code == 502
    assert "invalid result" in error.value.detail


def test_ats_pdf_report_escapes_ai_and_candidate_text(tmp_path, monkeypatch):
    monkeypatch.setattr(ats_service, "REPORTS_DIR", str(tmp_path))
    report = {
        "ats_score": 70,
        "keyword_match_pct": 60,
        "skills_match_pct": 65,
        "experience_match_pct": 80,
        "education_match_pct": 60,
        "project_match_pct": 100,
        "matching_skills": ["C++"],
        "missing_skills": [],
        "missing_technologies": [],
        "recommended_keywords": ["R&D"],
        "strengths": ["Built an R&D platform & API."],
        "weaknesses": [],
        "improvements": [],
        "formatting_suggestions": [],
        "ai_summary": "Strong fit for R&D & platform work.",
    }

    path = ats_service.generate_ats_pdf(report, "Dev & Engineer", 123)

    assert path.endswith("ats_report_123.pdf")
    assert (tmp_path / "ats_report_123.pdf").stat().st_size > 0
