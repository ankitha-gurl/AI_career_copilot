from typing import Optional
from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: int
    original_filename: str
    file_type: str
    created_at: str

    class Config:
        from_attributes = True


class ResumeAnalysisOut(BaseModel):
    id: int
    resume_id: int
    summary: Optional[str] = None
    analysis: dict

    class Config:
        from_attributes = True
