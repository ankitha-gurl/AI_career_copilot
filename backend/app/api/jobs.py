import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import JobDescription, JobMatch
from app.models.resume import Resume
from app.models.user import User
from app.schemas.job import JobDescriptionCreate, JobMatchRequest
from app.services.ai_service import AIService, AIServiceError

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobDescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description text is required.")

    try:
        analysis = AIService.analyze_job_description(payload.raw_text)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    job = JobDescription(
        user_id=current_user.id,
        title=payload.title or analysis.get("job_title"),
        company=payload.company or analysis.get("company"),
        raw_text=payload.raw_text,
        analysis_json=json.dumps(analysis),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {"id": job.id, "title": job.title, "company": job.company, "analysis": analysis}


@router.get("")
def list_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = db.query(JobDescription).filter(JobDescription.user_id == current_user.id).order_by(JobDescription.id.desc()).all()
    return [{"id": j.id, "title": j.title, "company": j.company, "created_at": j.created_at.isoformat()} for j in jobs]


def _get_owned_job(db: Session, job_id: int, user_id: int) -> JobDescription:
    job = db.query(JobDescription).filter(JobDescription.id == job_id, JobDescription.user_id == user_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found.")
    return job


@router.get("/{job_id}")
def get_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = _get_owned_job(db, job_id, current_user.id)
    return {"id": job.id, "title": job.title, "company": job.company,
            "analysis": json.loads(job.analysis_json) if job.analysis_json else None}


@router.post("/{job_id}/match")
def match_job(
    job_id: int,
    payload: JobMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _get_owned_job(db, job_id, current_user.id)
    if not job.analysis_json:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job has not been analyzed yet.")

    if payload.resume_id:
        resume = db.query(Resume).filter(Resume.id == payload.resume_id, Resume.user_id == current_user.id).first()
    else:
        resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.id.desc()).first()

    if not resume:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No resume found. Upload and analyze a resume first.")
    if not resume.analysis:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume has not been analyzed yet.")

    try:
        result = AIService.calculate_job_match(
            json.loads(resume.analysis.analysis_json), json.loads(job.analysis_json)
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    match = JobMatch(
        job_id=job.id,
        resume_id=resume.id,
        match_score=float(result.get("match_score", 0)),
        result_json=json.dumps(result),
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    return {"id": match.id, "job_id": job.id, "match_score": match.match_score, "result": result}


@router.get("/{job_id}/matches")
def list_matches(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = _get_owned_job(db, job_id, current_user.id)
    matches = db.query(JobMatch).filter(JobMatch.job_id == job.id).order_by(JobMatch.id.desc()).all()
    return [{"id": m.id, "match_score": m.match_score, "result": json.loads(m.result_json),
             "created_at": m.created_at.isoformat()} for m in matches]
