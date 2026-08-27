import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.resume import Resume, ResumeAnalysis
from app.models.user import User
from app.services.ai_service import AIService, AIServiceError
from app.services.file_service import validate_and_save_resume

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved_path, file_type, extracted_text = await validate_and_save_resume(file, current_user.id)

    resume = Resume(
        user_id=current_user.id,
        original_filename=file.filename,
        file_type=file_type,
        file_path=saved_path,
        extracted_text=extracted_text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {"id": resume.id, "original_filename": resume.original_filename, "file_type": resume.file_type}


@router.get("")
def list_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.id.desc()).all()
    return [
        {"id": r.id, "original_filename": r.original_filename, "file_type": r.file_type,
         "created_at": r.created_at.isoformat(), "has_analysis": r.analysis is not None}
        for r in resumes
    ]


def _get_owned_resume(db: Session, resume_id: int, user_id: int) -> Resume:
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    return resume


@router.post("/{resume_id}/analyze")
def analyze_resume(
    resume_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    resume = _get_owned_resume(db, resume_id, current_user.id)

    # Cost control: reuse existing analysis instead of re-calling the AI.
    if resume.analysis:
        return {"id": resume.analysis.id, "resume_id": resume.id,
                "summary": resume.analysis.summary, "analysis": json.loads(resume.analysis.analysis_json)}

    try:
        result = AIService.analyze_resume(resume.extracted_text or "")
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    analysis = ResumeAnalysis(
        resume_id=resume.id,
        summary=result.get("summary"),
        analysis_json=json.dumps(result),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {"id": analysis.id, "resume_id": resume.id, "summary": analysis.summary, "analysis": result}


@router.get("/{resume_id}/analysis")
def get_resume_analysis(
    resume_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    resume = _get_owned_resume(db, resume_id, current_user.id)
    if not resume.analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analysis yet for this resume.")
    return {"id": resume.analysis.id, "resume_id": resume.id, "summary": resume.analysis.summary,
            "analysis": json.loads(resume.analysis.analysis_json)}
