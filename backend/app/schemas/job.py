from typing import Optional
from pydantic import BaseModel


class JobDescriptionCreate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    raw_text: str


class JobDescriptionOut(BaseModel):
    id: int
    title: Optional[str] = None
    company: Optional[str] = None
    analysis: Optional[dict] = None

    class Config:
        from_attributes = True


class JobMatchRequest(BaseModel):
    resume_id: Optional[int] = None  # if omitted, use most recent resume


class JobMatchOut(BaseModel):
    id: int
    job_id: int
    match_score: float
    result: dict

    class Config:
        from_attributes = True
