import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import JobDescription
from app.models.roadmap import CareerRoadmap, RoadmapItem
from app.models.skill import UserSkill
from app.models.user import User
from app.schemas.roadmap import RoadmapRequest
from app.services.ai_service import AIService, AIServiceError

router = APIRouter(prefix="/roadmap", tags=["Career Roadmap"])


@router.post("")
def generate_roadmap(
    payload: RoadmapRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    skill_names = [us.skill.name for us in user_skills if us.skill]

    skill_gap = None
    if payload.job_id:
        job = db.query(JobDescription).filter(
            JobDescription.id == payload.job_id, JobDescription.user_id == current_user.id
        ).first()
        if job and job.analysis_json:
            try:
                skill_gap = AIService.generate_skill_gap(skill_names, json.loads(job.analysis_json))
            except AIServiceError:
                skill_gap = None

    try:
        result = AIService.generate_career_roadmap(payload.target_role, skill_names, skill_gap)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    roadmap = CareerRoadmap(user_id=current_user.id, target_role=payload.target_role)
    db.add(roadmap)
    db.flush()

    for idx, phase in enumerate(result.get("phases", [])):
        item = RoadmapItem(
            roadmap_id=roadmap.id,
            order_index=phase.get("order_index", idx),
            phase_title=phase.get("phase_title", f"Phase {idx + 1}"),
            skill=phase.get("skill"),
            priority=phase.get("priority"),
            difficulty=phase.get("difficulty"),
            prerequisites=phase.get("prerequisites"),
            project_task=phase.get("project_task"),
            success_criteria=phase.get("success_criteria"),
        )
        db.add(item)

    db.commit()
    db.refresh(roadmap)

    return {
        "id": roadmap.id,
        "target_role": roadmap.target_role,
        "items": [
            {"order_index": i.order_index, "phase_title": i.phase_title, "skill": i.skill,
             "priority": i.priority, "difficulty": i.difficulty, "prerequisites": i.prerequisites,
             "project_task": i.project_task, "success_criteria": i.success_criteria}
            for i in roadmap.items
        ],
    }


@router.get("")
def list_roadmaps(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roadmaps = db.query(CareerRoadmap).filter(CareerRoadmap.user_id == current_user.id).order_by(CareerRoadmap.id.desc()).all()
    return [{"id": r.id, "target_role": r.target_role, "created_at": r.created_at.isoformat(),
             "num_phases": len(r.items)} for r in roadmaps]


@router.get("/{roadmap_id}")
def get_roadmap(roadmap_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roadmap = db.query(CareerRoadmap).filter(
        CareerRoadmap.id == roadmap_id, CareerRoadmap.user_id == current_user.id
    ).first()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found.")
    return {
        "id": roadmap.id,
        "target_role": roadmap.target_role,
        "items": [
            {"order_index": i.order_index, "phase_title": i.phase_title, "skill": i.skill,
             "priority": i.priority, "difficulty": i.difficulty, "prerequisites": i.prerequisites,
             "project_task": i.project_task, "success_criteria": i.success_criteria}
            for i in roadmap.items
        ],
    }
