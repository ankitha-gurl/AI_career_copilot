"""
Aggregates a user's career context from the database for use by the
AI Copilot chat — retrieves ONLY relevant, already-stored data instead
of dumping the whole database into every prompt.
"""
import json

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.resume import Resume
from app.models.job import JobDescription, JobMatch
from app.models.skill import UserSkill


def build_user_context(db: Session, user: User) -> dict:
    context: dict = {
        "name": user.full_name,
    }

    if user.profile:
        context["profile"] = {
            "location": user.profile.location,
            "degree": user.profile.degree,
            "university": user.profile.university,
            "experience_years": user.profile.experience_years,
            "preferred_roles": user.profile.preferred_roles,
            "career_goals": user.profile.career_goals,
        }

    latest_resume = (
        db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.id.desc()).first()
    )
    if latest_resume and latest_resume.analysis:
        try:
            context["latest_resume_analysis"] = json.loads(latest_resume.analysis.analysis_json)
        except (json.JSONDecodeError, TypeError):
            pass

    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user.id).all()
    if user_skills:
        context["skills"] = [us.skill.name for us in user_skills if us.skill]

    latest_match = (
        db.query(JobMatch)
        .join(JobDescription, JobMatch.job_id == JobDescription.id)
        .filter(JobDescription.user_id == user.id)
        .order_by(JobMatch.id.desc())
        .first()
    )
    if latest_match:
        try:
            context["latest_job_match"] = json.loads(latest_match.result_json)
        except (json.JSONDecodeError, TypeError):
            pass

    return context
