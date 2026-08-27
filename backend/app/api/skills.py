import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import JobDescription
from app.models.skill import Skill, UserSkill
from app.models.user import User
from app.schemas.skill import SkillGapRequest
from app.services.ai_service import AIService, AIServiceError

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/me")
def get_my_skills(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    return [{"id": us.id, "name": us.skill.name, "proficiency": us.proficiency, "source": us.source}
            for us in user_skills]


@router.post("/me/{skill_name}")
def add_skill(
    skill_name: str,
    proficiency: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skill_name = skill_name.strip()
    if not skill_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skill name required.")

    skill = db.query(Skill).filter(Skill.name.ilike(skill_name)).first()
    if not skill:
        skill = Skill(name=skill_name)
        db.add(skill)
        db.flush()

    existing = db.query(UserSkill).filter(UserSkill.user_id == current_user.id, UserSkill.skill_id == skill.id).first()
    if existing:
        return {"id": existing.id, "name": skill.name, "proficiency": existing.proficiency}

    user_skill = UserSkill(user_id=current_user.id, skill_id=skill.id, proficiency=proficiency, source="manual")
    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)
    return {"id": user_skill.id, "name": skill.name, "proficiency": user_skill.proficiency}


@router.post("/gap-analysis")
def skill_gap_analysis(
    payload: SkillGapRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(JobDescription).filter(
        JobDescription.id == payload.job_id, JobDescription.user_id == current_user.id
    ).first()
    if not job or not job.analysis_json:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analyzed job not found.")

    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    skill_names = [us.skill.name for us in user_skills if us.skill]

    try:
        result = AIService.generate_skill_gap(skill_names, json.loads(job.analysis_json))
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return result
