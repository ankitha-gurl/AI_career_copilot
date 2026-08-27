import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.interview import InterviewQuestion, InterviewSession
from app.models.job import JobDescription
from app.models.resume import Resume
from app.models.user import User
from app.schemas.interview import InterviewAnswerRequest, InterviewGenerateRequest
from app.services.ai_service import AIService, AIServiceError

router = APIRouter(prefix="/interview", tags=["Interview Preparation"])


@router.post("/questions")
def generate_questions(
    payload: InterviewGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.id.desc()).first()
    resume_summary = ""
    if resume and resume.analysis:
        resume_summary = resume.analysis.summary or ""

    missing_skills: list[str] = []
    if payload.job_id:
        job = db.query(JobDescription).filter(
            JobDescription.id == payload.job_id, JobDescription.user_id == current_user.id
        ).first()
        if job and job.analysis_json:
            job_analysis = json.loads(job.analysis_json)
            missing_skills = job_analysis.get("required_skills", [])

    try:
        result = AIService.generate_interview_questions(
            payload.target_role, resume_summary, missing_skills, payload.num_questions
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    session = InterviewSession(user_id=current_user.id, target_role=payload.target_role)
    db.add(session)
    db.flush()

    questions_out = []
    for q in result.get("questions", []):
        question = InterviewQuestion(
            session_id=session.id,
            question_type=q.get("question_type", "technical"),
            question_text=q.get("question_text", ""),
            expected_concepts=q.get("expected_concepts"),
            model_answer=q.get("model_answer"),
            explanation=q.get("explanation"),
            follow_up_questions=json.dumps(q.get("follow_up_questions", [])),
        )
        db.add(question)
        db.flush()
        questions_out.append({
            "id": question.id, "question_type": question.question_type,
            "question_text": question.question_text, "expected_concepts": question.expected_concepts,
            "model_answer": question.model_answer, "explanation": question.explanation,
            "follow_up_questions": q.get("follow_up_questions", []),
        })

    db.commit()
    return {"session_id": session.id, "target_role": session.target_role, "questions": questions_out}


@router.get("/sessions")
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.id.desc()).all()
    return [{"id": s.id, "target_role": s.target_role, "created_at": s.created_at.isoformat(),
             "num_questions": len(s.questions)} for s in sessions]


@router.post("/evaluate")
def evaluate_answer(
    payload: InterviewAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = (
        db.query(InterviewQuestion)
        .join(InterviewSession, InterviewQuestion.session_id == InterviewSession.id)
        .filter(InterviewQuestion.id == payload.question_id, InterviewSession.user_id == current_user.id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    try:
        evaluation = AIService.evaluate_interview_answer(
            question.question_text, question.model_answer or "", payload.user_answer
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    question.user_answer = payload.user_answer
    question.evaluation_json = json.dumps(evaluation)
    db.commit()

    return {"question_id": question.id, "evaluation": evaluation}
