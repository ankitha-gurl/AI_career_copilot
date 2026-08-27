from typing import Optional
from pydantic import BaseModel


class InterviewGenerateRequest(BaseModel):
    target_role: str
    job_id: Optional[int] = None
    num_questions: int = 5


class InterviewQuestionOut(BaseModel):
    id: int
    question_type: str
    question_text: str
    expected_concepts: Optional[str] = None
    model_answer: Optional[str] = None
    explanation: Optional[str] = None
    follow_up_questions: Optional[str] = None

    class Config:
        from_attributes = True


class InterviewAnswerRequest(BaseModel):
    question_id: int
    user_answer: str


class InterviewEvaluationOut(BaseModel):
    question_id: int
    evaluation: dict
