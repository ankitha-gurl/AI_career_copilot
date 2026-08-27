from typing import Optional
from pydantic import BaseModel


class SkillGapRequest(BaseModel):
    job_id: int


class UserSkillOut(BaseModel):
    id: int
    name: str
    proficiency: Optional[str] = None
    source: str

    class Config:
        from_attributes = True
